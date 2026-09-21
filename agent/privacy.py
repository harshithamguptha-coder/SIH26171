"""
agent/privacy.py
================
On-Device Privacy Protection Module for SIH26171.
Problem Statement: On-device Visual Perception for Lightweight Browser Agents

Pipeline:
Screenshot -> Local OCR -> Extract text with coordinates -> Detect sensitive info -> Mask regions -> Protected screenshot

Detects:
1. Email addresses (e.g. user@example.com)
2. Phone numbers (e.g. +91 98765 43210, (555) 123-4567, 10-digit numbers)
3. Credit/debit card numbers (e.g. 4532 1234 5678 9010)
4. Password/secret/API token patterns (e.g. password: ****, token=xyz, masked bullets)

All processing is 100% on-device using OpenCV and regex. Zero cloud APIs.
"""

import os
import sys
import re
import cv2
import numpy as np
from typing import Tuple, List, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.ocr import VisualPerception
from utils.helpers import get_screenshots_dir


class PrivacyGuard:
    """
    Detects sensitive Personally Identifiable Information (PII) from local OCR data
    and masks the sensitive pixel regions directly on the screenshot image.
    """

    # Category names
    CAT_EMAIL = "Email address"
    CAT_PHONE = "Phone number"
    CAT_CARD = "Credit/debit card number"
    CAT_PASSWORD = "Password / Token"

    # Compiled Regular Expressions for Sensitive Data
    PATTERNS = {
        CAT_EMAIL: re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        CAT_PHONE: re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{5}[-.\s]?\d{5}|\b\d{10}\b)"
        ),
        CAT_CARD: re.compile(
            r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b"
        ),
        CAT_PASSWORD: re.compile(
            r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|bearer)[:=\s]+([^\s]+)|[\*•]{4,}"
        ),
    }

    def __init__(self, redact_mode: str = "blackout"):
        """
        Parameters:
            redact_mode (str): 'blackout' (solid dark rectangle) or 'blur' (Gaussian blur).
        """
        self.redact_mode = redact_mode
        self.ocr = VisualPerception()

    def find_sensitive_boxes(self, ocr_tokens: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Analyzes detected OCR tokens against sensitive regex patterns.
        Computes bounding boxes for matches (both single-word and line-level multi-word matches).

        Returns:
            Tuple[List[Dict], List[str]]:
                - List of sensitive items: [{'box': [x, y, w, h], 'category': str, 'matched_text': str}]
                - Distinct list of detected category names.
        """
        sensitive_items = []
        detected_categories = set()

        # 1. Single-token inspection (fast pass for single-word emails, tokens, passwords)
        for token in ocr_tokens:
            text = token.get("text", "").strip()
            for category, pattern in self.PATTERNS.items():
                if pattern.search(text):
                    sensitive_items.append({
                        "box": token["box"],
                        "category": category,
                        "matched_text": text
                    })
                    detected_categories.add(category)
                    break

        # 2. Line-level inspection (detects multi-word items like spaced credit cards or formatted phone numbers)
        lines: Dict[int, List[Dict]] = {}
        for token in ocr_tokens:
            line_id = token.get("line_id", 0)
            lines.setdefault(line_id, []).append(token)

        for line_id, line_tokens in lines.items():
            line_text = ""
            token_spans = []
            for t in line_tokens:
                start = len(line_text)
                line_text += t["text"]
                end = len(line_text)
                token_spans.append((start, end, t))
                line_text += " "

            for category, pattern in self.PATTERNS.items():
                for match in pattern.finditer(line_text):
                    m_start, m_end = match.span()
                    # Find tokens that overlap with this regex match
                    matching_tokens = [
                        t for start, end, t in token_spans
                        if not (end <= m_start or start >= m_end)
                    ]
                    if matching_tokens:
                        x_min = min(t["box"][0] for t in matching_tokens)
                        y_min = min(t["box"][1] for t in matching_tokens)
                        x_max = max(t["box"][0] + t["box"][2] for t in matching_tokens)
                        y_max = max(t["box"][1] + t["box"][3] for t in matching_tokens)

                        combined_box = [x_min, y_min, x_max - x_min, y_max - y_min]
                        sensitive_items.append({
                            "box": combined_box,
                            "category": category,
                            "matched_text": match.group(0).strip()
                        })
                        detected_categories.add(category)

        # Remove duplicate bounding boxes
        unique_items = []
        for item in sensitive_items:
            ix, iy, iw, ih = item["box"]
            is_dup = False
            for u in unique_items:
                ux, uy, uw, uh = u["box"]
                if abs(ix - ux) < 10 and abs(iy - uy) < 10 and abs(iw - uw) < 15 and abs(ih - uh) < 15:
                    is_dup = True
                    break
            if not is_dup:
                unique_items.append(item)

        return unique_items, sorted(list(detected_categories))

    def mask_image(self, image_path: str, sensitive_items: List[Dict], output_path: str = None) -> str:
        """
        Draws black or blurred rectangles over sensitive bounding boxes using OpenCV.
        Saves the resulting protected image locally.

        Parameters:
            image_path (str): Path to original screenshot.
            sensitive_items (list): Items with 'box' [x, y, w, h] and 'category'.
            output_path (str, optional): Target file path for protected image.

        Returns:
            str: Path to the locally saved protected screenshot.
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image at {image_path}")

        img_h, img_w = image.shape[:2]

        for item in sensitive_items:
            x, y, w, h = item["box"]
            cat = item.get("category", "SENSITIVE")

            # Add padding around bounding box for thorough masking
            pad = 5
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(img_w, x + w + pad)
            y2 = min(img_h, y + h + pad)

            if self.redact_mode == "blur":
                # Apply heavy Gaussian blur to the region
                roi = image[y1:y2, x1:x2]
                if roi.shape[0] > 0 and roi.shape[1] > 0:
                    blurred = cv2.GaussianBlur(roi, (51, 51), 30)
                    image[y1:y2, x1:x2] = blurred
            else:
                # Solid black rectangle mask
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 0), -1)

                # Optional label tag above/inside the mask
                tag = f"[PROTECTED: {cat.upper()}]"
                cv2.putText(
                    image,
                    tag,
                    (x1 + 3, max(12, y1 + 14)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA,
                )

        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_protected{ext}"

        cv2.imwrite(output_path, image)
        print(f"[PrivacyGuard] Saved protected image to: {output_path}")
        return output_path

    def find_sensitive_elements(self, elements: List[Dict]) -> List[Dict]:
        """
        Backwards-compatible helper for Level 1 scripts and tests.
        Takes detected tokens or elements and returns sensitive items with 'pii_type', 'matched_text', and 'box'.
        """
        sensitive_items, _ = self.find_sensitive_boxes(elements)
        cat_to_pii = {
            self.CAT_EMAIL: "email",
            self.CAT_PHONE: "phone_number",
            self.CAT_CARD: "credit_card",
            self.CAT_PASSWORD: "api_key_or_secret",
        }
        results = []
        for item in sensitive_items:
            category = item.get("category", "")
            pii_type = cat_to_pii.get(category, category.lower().replace(" ", "_"))
            results.append({
                "box": item["box"],
                "category": category,
                "pii_type": pii_type,
                "matched_text": item.get("matched_text", ""),
            })
        return results

    def mask_screenshot(self, image_path: str, sensitive_items: List[Dict]) -> Tuple[str, int]:
        """
        Backwards-compatible helper for Level 1 scripts and tests.
        Masks image and returns (masked_path, count_of_redacted_regions).
        """
        masked_path = self.mask_image(image_path, sensitive_items)
        return masked_path, len(sensitive_items)

    def process_screenshot(self, screenshot_path: str) -> Tuple[str, str, List[str]]:
        """
        Executes the complete local privacy protection pipeline:
        Screenshot -> OCR -> Detect sensitive info -> Mask regions -> Protected screenshot

        Returns:
            Tuple[str, str, List[str]]:
                1. Original screenshot path
                2. Protected screenshot path
                3. List of detected sensitive categories
        """
        if not os.path.exists(screenshot_path):
            raise FileNotFoundError(f"Screenshot file not found: {screenshot_path}")

        print(f"[PrivacyPipeline] Step 1: Running local OCR on {screenshot_path}...")
        tokens = self.ocr.extract_words_and_lines(screenshot_path)
        print(f"[PrivacyPipeline] Step 2: Extracted {len(tokens)} text tokens.")

        print("[PrivacyPipeline] Step 3: Detecting sensitive information patterns...")
        sensitive_items, categories = self.find_sensitive_boxes(tokens)
        print(f"[PrivacyPipeline] Detected {len(sensitive_items)} sensitive region(s): {categories}")

        print("[PrivacyPipeline] Step 4: Masking sensitive regions locally with OpenCV...")
        protected_path = self.mask_image(screenshot_path, sensitive_items)

        print("[PrivacyPipeline] Step 5: Privacy pipeline complete (100% on-device).")
        return screenshot_path, protected_path, categories


def protect_screenshot(screenshot_path: str, redact_mode: str = "blackout") -> Tuple[str, str, List[str]]:
    """
    Top-level helper function to run the privacy protection pipeline.

    Returns:
        Tuple[str, str, List[str]]:
            1. Original screenshot path
            2. Protected screenshot path
            3. List of detected sensitive categories
    """
    guard = PrivacyGuard(redact_mode=redact_mode)
    return guard.process_screenshot(screenshot_path)


def create_synthetic_demo_screenshot() -> str:
    """
    Creates a realistic synthetic webpage screenshot with sample sensitive data
    (Email, Phone, Credit Card, Password) to test and demonstrate the privacy module.
    """
    screenshots_dir = get_screenshots_dir()
    filepath = os.path.join(screenshots_dir, "synthetic_profile_sample.png")

    # 1. Create a clean white card layout (width: 900, height: 550)
    canvas = np.ones((550, 900, 3), dtype=np.uint8) * 250

    # Draw header bar
    cv2.rectangle(canvas, (0, 0), (900, 60), (30, 58, 138), -1)  # Dark blue header
    cv2.putText(canvas, "User Account & Security Settings - Internal Portal", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

    # Card container
    cv2.rectangle(canvas, (40, 80), (860, 510), (255, 255, 255), -1)
    cv2.rectangle(canvas, (40, 80), (860, 510), (220, 220, 220), 1)

    # Content labels and values
    fields = [
        ("Full Name:", "Aarav Sharma"),
        ("Email Address:", "aarav.sharma@example.gov.in"),
        ("Phone Number:", "+91 98765 43210"),
        ("Billing Card:", "4532 8910 1112 1314"),
        ("Account Password:", "SecretPass@2026"),
        ("API Token:", "token_sk_live_9988776655"),
    ]

    y = 130
    for label, val in fields:
        cv2.putText(canvas, label, (70, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (70, 70, 70), 1)
        cv2.putText(canvas, val, (310, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (10, 10, 10), 2)
        cv2.line(canvas, (70, y + 15), (830, y + 15), (240, 240, 240), 1)
        y += 60

    cv2.imwrite(filepath, canvas)
    print(f"[DemoHelper] Created synthetic sample screenshot: {filepath}")
    return filepath


if __name__ == "__main__":
    print("Testing PrivacyGuard on synthetic sensitive screenshot...")
    sample_path = create_synthetic_demo_screenshot()
    orig, protected, cats = protect_screenshot(sample_path, redact_mode="blackout")
    print("\n--- Privacy Pipeline Results ---")
    print(f"1. Original Image : {orig}")
    print(f"2. Protected Image: {protected}")
    print(f"3. Categories     : {cats}")

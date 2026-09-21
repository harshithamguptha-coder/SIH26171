"""
agent/vision.py
===============
Lightweight local visual perception for the SIH26171 browser-agent prototype.

Pipeline:
    browser screenshot
    -> privacy masking
    -> local OCR / visual processing
    -> detected text + bounding boxes
    -> target UI element identification
    -> approximate screen coordinates

This module is intentionally small and local-only. It does not call any cloud
vision API and it does not attempt to be a general autonomous computer-use
agent. The first target page is Google/Bing-style search UI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.ocr import VisualPerception
from agent.privacy import PrivacyGuard


MIN_OCR_CONFIDENCE = 20.0
MIN_OCR_CONFIDENCE = 10.0
TARGET_ALIASES = {
    "search_box": {"search_box", "search input", "search_input", "input", "textbox", "text_box"},
    "search_button": {"search_button", "button", "search", "google search", "bing search"},
    "search_box": {"search_box", "search input", "search_input", "textbox", "text_box"},
    "search_button": {"search_button", "google search", "bing search"},
    "sign_in": {"sign in", "signin", "sign_in", "log in", "login", "sign in button"},
    "submit_button": {"submit", "submit form", "submit button", "submit application"},
}


@dataclass
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def cx(self) -> int:
        return self.x + self.width // 2

    @property
    def cy(self) -> int:
        return self.y + self.height // 2

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.width, self.height]


def _clamp_box(box: Box, image_width: int, image_height: int) -> Box:
    x = max(0, min(box.x, image_width - 1))
    y = max(0, min(box.y, image_height - 1))
    width = max(1, min(box.width, image_width - x))
    height = max(1, min(box.height, image_height - y))
    return Box(x, y, width, height)


def _element_result(
    element: str,
    box: Box,
    confidence: float,
    method: str,
    matched_text: str = "",
) -> dict[str, Any]:
    return {
        "element": element,
        "x": box.cx,
        "y": box.cy,
        "width": box.width,
        "height": box.height,
        "confidence": round(float(confidence), 3),
        "method": method,
        "matched_text": matched_text,
        "box": box.as_list(),
    }


class LocalVision:
    """
    Local-only UI perception for simple browser screenshots.

    It combines privacy masking, Tesseract OCR, simple OpenCV geometry, and
    rule-based matching for Google/Bing search controls.
    """

    def __init__(self, debug: bool = False, redact_mode: str = "blackout"):
        self.debug = debug
        self.redact_mode = redact_mode
        self.ocr = VisualPerception()
        self.privacy = PrivacyGuard(redact_mode=redact_mode)

    def analyse(self, screenshot_path: str) -> dict[str, Any]:
        source = Path(screenshot_path)
        if not source.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        raw_image = cv2.imread(str(source))
        if raw_image is None:
            raise ValueError(f"Could not load screenshot: {screenshot_path}")

        image_height, image_width = raw_image.shape[:2]
        protected_path, sensitive_items = self._mask_privately(source)
        protected_image = cv2.imread(str(protected_path))
        if protected_image is None:
            protected_image = raw_image

        tokens = self._ocr_tokens(str(protected_path))
        text_tokens = [self._format_token(token) for token in tokens]

        search_box = self._detect_search_box(protected_image, tokens)
        search_button = self._detect_search_button(tokens, search_box, image_width, image_height)
        actionable_elements = self._detect_actionable_elements(tokens, image_width, image_height)

        elements = []
        if search_box:
            elements.append(search_box)
        if search_button:
            elements.append(search_button)
        for act in actionable_elements:
            # Avoid duplicating search button
            if act["element"] != "search_button" or not search_button:
                elements.append(act)

        debug_image = None
        if self.debug:
            debug_image = self._save_debug_image(
                protected_image,
                source,
                elements,
                tokens,
                sensitive_items,
            )

        return {
            "screenshot": str(source),
            "protected_screenshot": str(protected_path),
            "image_size": [image_width, image_height],
            "elements": elements,
            "text_tokens": text_tokens,
            "sensitive_regions": sensitive_items,
            "debug_image": debug_image,
            "local_only": True,
            "processing": "privacy_masking -> local_tesseract_ocr -> opencv_geometry -> rules",
        }

    def find_target(self, screenshot_path: str, target: str = "search_box") -> dict[str, Any] | None:
        wanted = self._normalise_target(target)
        result = self.analyse(screenshot_path)

        # 1. Exact element name match
        for element in result["elements"]:
            if element["element"] == wanted:
                return {
                    "element": element["element"],
                    "x": element["x"],
                    "y": element["y"],
                    "confidence": element["confidence"],
                    "box": element.get("box"),
                    "method": element.get("method", "specialized_detector"),
                }

        # 2. Text / alias match in detected elements
        for element in result["elements"]:
            elem_name = str(element.get("element", "")).lower().strip()
            matched = str(element.get("matched_text", "")).lower().strip()
            if (
                wanted == elem_name
                or (matched and wanted == matched)
                or (len(wanted) > 2 and wanted in elem_name)
                or (matched and len(wanted) > 2 and (wanted in matched or matched in wanted))
            ):
                return {
                    "element": element["element"],
                    "x": element["x"],
                    "y": element["y"],
                    "confidence": element["confidence"],
                    "box": element.get("box"),
                    "method": element.get("method", "element_match"),
                }

        # 3. Direct OCR token / line search for arbitrary text targets
        source = Path(screenshot_path)
        if source.exists():
            protected_path = source.with_name(f"{source.stem}_protected{source.suffix}")
            check_path = str(protected_path) if protected_path.exists() else str(source)
            tokens = self._ocr_tokens(check_path)
            raw_img = cv2.imread(check_path)
            h, w = raw_img.shape[:2] if raw_img is not None else (800, 1280)

            direct_match = self._find_text_element_in_tokens(tokens, target, w, h)
            if direct_match:
                return {
                    "element": direct_match["element"],
                    "x": direct_match["x"],
                    "y": direct_match["y"],
                    "confidence": direct_match["confidence"],
                    "box": direct_match.get("box"),
                    "method": direct_match.get("method", "visual_ocr_match"),
                }

            # 4. Form input label search (e.g. "name", "full name", "email")
            input_match = self._find_input_near_label(tokens, raw_img, target, w, h)
            if input_match:
                return input_match

        return None

    def _mask_privately(self, source: Path) -> tuple[Path, list[dict[str, Any]]]:
        tokens = self.ocr.extract_words_and_lines(str(source))
        sensitive_items, _categories = self.privacy.find_sensitive_boxes(tokens)
        output_path = source.with_name(f"{source.stem}_protected{source.suffix}")
        protected_path = self.privacy.mask_image(str(source), sensitive_items, str(output_path))
        return Path(protected_path), sensitive_items

    def _ocr_tokens(self, image_path: str) -> list[dict[str, Any]]:
        tokens = self.ocr.extract_words_and_lines(image_path)
        return [
            token for token in tokens
            if token.get("text", "").strip()
            and float(token.get("confidence", -1)) >= MIN_OCR_CONFIDENCE
        ]

    def _detect_search_box(
        self,
        image: np.ndarray,
        tokens: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        image_height, image_width = image.shape[:2]
        candidates = self._input_like_contours(image)

        if candidates:
            best = max(candidates, key=lambda item: item["score"])
            box = _clamp_box(best["box"], image_width, image_height)
            return _element_result(
                "search_box",
                box,
                best["confidence"],
                "opencv_input_contour",
            )

        search_text = self._find_search_hint_token(tokens)
        if search_text:
            x, y, w, h = search_text["box"]
            box = _clamp_box(
                Box(max(0, x - 20), max(0, y - 14), max(w + 240, int(image_width * 0.35)), max(h + 24, 36)),
                image_width,
                image_height,
            )
            return _element_result(
                "search_box",
                box,
                0.58,
                "ocr_search_hint",
                search_text["text"],
            )

        fallback = Box(
            int(image_width * 0.25),
            int(image_height * 0.36),
            int(image_width * 0.50),
            44,
        )
        return _element_result(
            "search_box",
            _clamp_box(fallback, image_width, image_height),
            0.42,
            "google_homepage_geometry_fallback",
        )

    def _input_like_contours(self, image: np.ndarray) -> list[dict[str, Any]]:
        image_height, image_width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 17), np.uint8))
        contours, _hierarchy = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[dict[str, Any]] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < image_width * 0.28 or w > image_width * 0.85:
                continue
            if h < 28 or h > 80:
                continue
            if y < image_height * 0.12 or y > image_height * 0.68:
                continue

            center_score = 1.0 - min(1.0, abs((x + w / 2) - image_width / 2) / (image_width / 2))
            width_score = min(1.0, w / (image_width * 0.52))
            height_score = 1.0 - min(1.0, abs(h - 44) / 44)
            score = 0.45 * center_score + 0.35 * width_score + 0.20 * height_score
            candidates.append({
                "box": Box(x, y, w, h),
                "score": score,
                "confidence": max(0.5, min(0.88, score)),
            })

        return candidates

    def _detect_search_button(
        self,
        tokens: list[dict[str, Any]],
        search_box: dict[str, Any] | None,
        image_width: int,
        image_height: int,
    ) -> dict[str, Any] | None:
        button_tokens = self._search_button_tokens(tokens)
        if button_tokens:
            merged_box = self._merge_token_boxes(button_tokens)
            text = " ".join(token["text"] for token in button_tokens)
            return _element_result(
                "search_button",
                _clamp_box(merged_box, image_width, image_height),
                0.78,
                "ocr_button_text",
                text,
            )

        if search_box:
            sx, sy, sw, sh = search_box["box"]
            box = Box(sx + sw - 56, sy + 4, 48, max(28, sh - 8))
            return _element_result(
                "search_button",
                _clamp_box(box, image_width, image_height),
                0.5,
                "inferred_icon_inside_search_box",
            )

        return None

    def _search_button_tokens(self, tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lines: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
        for token in tokens:
            key = (
                int(token.get("block_num", 0)),
                int(token.get("par_num", 0)),
                int(token.get("line_num", token.get("line_id", 0))),
            )
            lines.setdefault(key, []).append(token)

        for line_tokens in lines.values():
            ordered = sorted(line_tokens, key=lambda item: item["box"][0])
            line_text = " ".join(item["text"] for item in ordered).lower()
            if "google search" in line_text:
                return [item for item in ordered if item["text"].lower() in {"google", "search"}]

        for token in tokens:
            text = token["text"].strip().lower()
            if text in {"search", "go"} or "search" in text:
                return [token]
        return []

    def _find_search_hint_token(self, tokens: list[dict[str, Any]]) -> dict[str, Any] | None:
        for token in tokens:
            text = token["text"].strip().lower()
            if text in {"search", "google", "bing"} or "search" in text:
                return token
        return None

    def _merge_token_boxes(self, tokens: list[dict[str, Any]]) -> Box:
        x1 = min(token["box"][0] for token in tokens)
        y1 = min(token["box"][1] for token in tokens)
        x2 = max(token["box"][0] + token["box"][2] for token in tokens)
        y2 = max(token["box"][1] + token["box"][3] for token in tokens)
        pad_x = 16
        pad_y = 10
        return Box(x1 - pad_x, y1 - pad_y, x2 - x1 + 2 * pad_x, y2 - y1 + 2 * pad_y)

    def _format_token(self, token: dict[str, Any]) -> dict[str, Any]:
        x, y, w, h = token["box"]
        return {
            "text": token["text"],
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "confidence": round(float(token["confidence"]) / 100.0, 3),
        }

    def _detect_actionable_elements(
        self,
        tokens: list[dict[str, Any]],
        image_width: int,
        image_height: int,
    ) -> list[dict[str, Any]]:
        actionable: list[dict[str, Any]] = []
        action_phrases = [
            ("sign_in", "sign in"),
            ("login_button", "log in"),
            ("submit_button", "submit"),
            ("sign_up", "sign up"),
        ]
        for canonical, phrase in action_phrases:
            match = self._find_text_element_in_tokens(tokens, phrase, image_width, image_height)
            if match:
                match["element"] = canonical
                actionable.append(match)
        return actionable

    def _find_text_element_in_tokens(
        self,
        tokens: list[dict[str, Any]],
        target_text: str,
        image_width: int,
        image_height: int,
    ) -> dict[str, Any] | None:
        target_lower = target_text.strip().lower()
        if not target_lower:
            return None

        # 1. Multi-token / line matching
        lines: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
        for token in tokens:
            key = (
                int(token.get("block_num", 0)),
                int(token.get("par_num", 0)),
                int(token.get("line_num", token.get("line_id", 0))),
            )
            lines.setdefault(key, []).append(token)

        best_match_tokens = None
        for line_tokens in lines.values():
            ordered = sorted(line_tokens, key=lambda item: item["box"][0])
            line_text = " ".join(item["text"] for item in ordered).lower()
            if target_lower in line_text:
                words = target_lower.split()
                for i in range(len(ordered) - len(words) + 1):
                    sub = " ".join(ordered[i + k]["text"].lower() for k in range(len(words)))
                    if target_lower in sub:
                        best_match_tokens = ordered[i : i + len(words)]
                        break
                if not best_match_tokens:
                    best_match_tokens = [t for t in ordered if any(w in t["text"].lower() for w in words)]
                break

        # 2. Single token matching
        if not best_match_tokens:
            no_space_target = target_lower.replace(" ", "")
            for token in tokens:
                token_text = token["text"].strip().lower()
                if (
                    target_lower == token_text
                    or (no_space_target and no_space_target == token_text)
                    or (len(target_lower) > 3 and (target_lower in token_text or token_text in target_lower))
                ):
                    best_match_tokens = [token]
                    break

        if best_match_tokens:
            merged_box = self._merge_token_boxes(best_match_tokens)
            clamped = _clamp_box(merged_box, image_width, image_height)
            avg_conf = sum(float(t.get("confidence", 80)) for t in best_match_tokens) / (100.0 * len(best_match_tokens))
            matched_str = " ".join(t["text"] for t in best_match_tokens)
            return _element_result(
                target_text,
                clamped,
                max(0.55, min(0.95, avg_conf)),
                "visual_ocr_match",
                matched_str,
            )

        return None

    def _find_input_near_label(
        self,
        tokens: list[dict[str, Any]],
        image: np.ndarray | None,
        target_name: str,
        image_width: int,
        image_height: int,
    ) -> dict[str, Any] | None:
        target_lower = target_name.strip().lower()
        label_token = None
        for token in tokens:
            t_text = token["text"].strip().lower().rstrip(":")
            if t_text in target_lower or (len(t_text) > 3 and t_text in {"name", "email", "username", "password"} and t_text in target_lower):
                label_token = token
                break

        if not label_token:
            return None

        lx, ly, lw, lh = label_token["box"]

        # Check if there are contours to the right or below this label
        if image is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 30, 120)
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 9), np.uint8))
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Candidate 1: Right of label
            for c in contours:
                cx, cy, cw, ch = cv2.boundingRect(c)
                if abs(cy + ch / 2 - (ly + lh / 2)) < 25 and cx > lx and cw > 60:
                    box = Box(cx, cy, cw, ch)
                    return _element_result(
                        f"{target_name}_field",
                        _clamp_box(box, image_width, image_height),
                        0.82,
                        "opencv_input_near_label",
                        label_token["text"],
                    )

            # Candidate 2: Directly below label
            for c in contours:
                cx, cy, cw, ch = cv2.boundingRect(c)
                if cy > ly and abs(cy - (ly + lh)) < 40 and abs(cx - lx) < 60 and cw > 80:
                    box = Box(cx, cy, cw, ch)
                    return _element_result(
                        f"{target_name}_field",
                        _clamp_box(box, image_width, image_height),
                        0.80,
                        "opencv_input_below_label",
                        label_token["text"],
                    )

        # Fallback: estimate input center offset from label
        estimated_box = Box(lx + lw + 20, ly - 4, max(180, int(image_width * 0.25)), max(lh + 8, 36))
        return _element_result(
            f"{target_name}_field",
            _clamp_box(estimated_box, image_width, image_height),
            0.62,
            "inferred_offset_from_label",
            label_token["text"],
        )

    def _save_debug_image(
        self,
        image: np.ndarray,
        source: Path,
        elements: list[dict[str, Any]],
        tokens: list[dict[str, Any]],
        sensitive_items: list[dict[str, Any]],
    ) -> str:
        annotated = image.copy()

        for token in tokens:
            x, y, w, h = token["box"]
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 190, 255), 1)

        for item in sensitive_items:
            x, y, w, h = item["box"]
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)

        colours = {
            "search_box": (0, 180, 0),
            "search_button": (255, 80, 0),
        }
        for element in elements:
            x, y, w, h = element["box"]
            colour = colours.get(element["element"], (255, 255, 255))
            cv2.rectangle(annotated, (x, y), (x + w, y + h), colour, 3)
            label = f"{element['element']} {element['confidence']:.2f}"
            cv2.putText(
                annotated,
                label,
                (x, max(18, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                colour,
                2,
                cv2.LINE_AA,
            )

        debug_path = source.with_name(f"{source.stem}_vision_debug{source.suffix}")
        cv2.imwrite(str(debug_path), annotated)
        return str(debug_path)

    def _normalise_target(self, target: str) -> str:
        lowered = target.strip().lower()
        for canonical, aliases in TARGET_ALIASES.items():
            if lowered in aliases:
                return canonical
        return lowered


class VisionAgent(LocalVision):
    """Backward-compatible name used by earlier prototype code."""


def detect_ui_elements(screenshot_path: str, debug: bool = False) -> dict[str, Any]:
    return LocalVision(debug=debug).analyse(screenshot_path)


def locate_ui_element(
    screenshot_path: str,
    target: str = "search_box",
    debug: bool = False,
) -> dict[str, Any] | None:
    """
    Return the compact coordinate payload requested by the prototype.

    Example:
        {"element": "search_box", "x": 500, "y": 300, "confidence": 0.85}
    """
    return LocalVision(debug=debug).find_target(screenshot_path, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local UI perception for browser screenshots.")
    parser.add_argument("screenshot", help="Path to a local PNG/JPG browser screenshot.")
    parser.add_argument("--target", default="search_box", help="UI target to locate.")
    parser.add_argument("--debug", action="store_true", help="Save an annotated debug screenshot.")
    parser.add_argument("--full", action="store_true", help="Print full OCR and element analysis.")
    args = parser.parse_args()

    vision = LocalVision(debug=args.debug)
    if args.full:
        print(json.dumps(vision.analyse(args.screenshot), indent=2))
    else:
        print(json.dumps(vision.find_target(args.screenshot, args.target), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

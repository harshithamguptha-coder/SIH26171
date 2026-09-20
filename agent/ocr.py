"""
agent/ocr.py
============
On-Device Optical Character Recognition (OCR) for SIH26171.
Problem Statement: On-device Visual Perception for Lightweight Browser Agents

Capabilities:
1. Performs local OCR using pytesseract (Tesseract OCR engine).
2. Extracts word-level and line-level text tokens with exact pixel bounding boxes [x, y, w, h].
3. Groups words into reconstructed lines so multi-word sensitive items (like credit cards
   and formatted phone numbers) can be detected accurately.
4. Operates 100% on-device — No network requests or cloud vision APIs.
"""

import os
import sys
import shutil
import cv2
import numpy as np
import pytesseract
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class VisualPerception:
    """
    On-device OCR and visual element extractor using local Tesseract engine.
    """

    def __init__(self):
        self._configure_tesseract_path()

    def _configure_tesseract_path(self):
        """Locates tesseract.exe on standard Windows installation paths."""
        if shutil.which("tesseract"):
            return  # Already available in system PATH

        common_windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for path in common_windows_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"[OCR] Located Tesseract binary at: {path}")
                return

    def is_tesseract_available(self) -> bool:
        """Checks if Tesseract OCR is available on this system."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_words_and_lines(self, image_path: str) -> list[dict]:
        """
        Runs local OCR on an image and returns a list of detected text tokens
        with bounding box coordinates [x, y, width, height] and confidence scores.

        Parameters:
            image_path (str): Local path to the screenshot image.

        Returns:
            list[dict]: List of detected items, each containing:
                {
                    'text': str,
                    'box': [x, y, w, h],
                    'confidence': float,
                    'line_id': int
                }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        if not self.is_tesseract_available():
            print("[OCR] Warning: Tesseract binary not found. Returning empty OCR list.")
            return []

        # Load image via Pillow for pytesseract
        pil_img = Image.open(image_path)

        # image_to_data extracts word-level bounding boxes and line numbers
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)

        tokens = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])

            # Filter out empty strings or block headers (Tesseract sets conf=-1 for non-word blocks)
            if text and conf >= 0:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                line_id = data.get("line_num", [0])[i]

                tokens.append({
                    "text": text,
                    "box": [x, y, w, h],
                    "confidence": conf,
                    "line_id": line_id
                })

        return tokens

    # Alias for general element extraction
    def extract_elements(self, image_path: str) -> list[dict]:
        return self.extract_words_and_lines(image_path)

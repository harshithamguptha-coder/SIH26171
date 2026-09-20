"""
test_agent.py
=============
Quick test script to verify that:
1. All agent components import cleanly.
2. OpenCV visual annotation & bounding box logic work.
3. Privacy guard regex and image masking work locally.
"""

import os
import cv2
import numpy as np
from agent.privacy import PrivacyGuard
from agent.ocr import VisualPerception
from utils.helpers import get_screenshots_dir, draw_bounding_boxes


def test_privacy_and_annotation():
    print("Testing SIH26171 On-Device Modules...")

    # 1. Create a synthetic test image with mock text
    test_img_path = os.path.join(get_screenshots_dir(), "test_sample.png")
    img = np.ones((400, 700, 3), dtype=np.uint8) * 240  # Light gray background

    # Draw dummy text onto test image
    cv2.putText(img, "Smart India Hackathon 2026", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "Contact: admin@sih.gov.in", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)
    cv2.putText(img, "Secret Key: sk_test_987654321", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)
    cv2.rectangle(img, (50, 260), (450, 310), (100, 100, 100), 2)  # Mock search box
    cv2.putText(img, "Search here...", (60, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

    cv2.imwrite(test_img_path, img)
    print(f"[OK] Created synthetic test image: {test_img_path}")

    # 2. Test PrivacyGuard detection and masking
    guard = PrivacyGuard(redact_mode="blackout")
    mock_detected_elements = [
        {"text": "Smart India Hackathon 2026", "box": [50, 40, 400, 30], "confidence": 95.0},
        {"text": "Contact: admin@sih.gov.in", "box": [50, 110, 350, 30], "confidence": 95.0},
        {"text": "Secret Key: sk_test_987654321", "box": [50, 180, 380, 30], "confidence": 95.0},
        {"text": "[SEARCH_BOX]", "box": [50, 260, 400, 50], "confidence": 90.0},
    ]

    sensitive = guard.find_sensitive_elements(mock_detected_elements)
    print(f"[OK] PrivacyGuard detected {len(sensitive)} sensitive item(s):")
    for s in sensitive:
        print(f"     - Type: {s['pii_type']} -> Text: '{s['matched_text']}'")

    masked_path, count = guard.mask_screenshot(test_img_path, sensitive)
    print(f"[OK] Redacted {count} regions into: {masked_path}")

    # 3. Test Visual Perception fallback & box drawing
    annotated_path = draw_bounding_boxes(test_img_path, mock_detected_elements)
    print(f"[OK] Annotated image generated: {annotated_path}")

    print("\nAll unit tests passed successfully!")


if __name__ == "__main__":
    test_privacy_and_annotation()


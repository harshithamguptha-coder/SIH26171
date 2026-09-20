import os

import cv2
import numpy as np

from agent.vision import detect_ui_elements, locate_ui_element
from utils.helpers import get_screenshots_dir


def test_local_vision_detects_google_like_search_ui():
    screenshots_dir = get_screenshots_dir()
    image_path = os.path.join(screenshots_dir, "synthetic_google_vision.png")

    canvas = np.ones((600, 1000, 3), dtype=np.uint8) * 255
    cv2.putText(canvas, "Google", (420, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (30, 30, 30), 2)
    cv2.rectangle(canvas, (250, 230), (750, 280), (200, 200, 200), 2)
    cv2.putText(canvas, "Search", (790, 264), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (60, 60, 60), 2)
    cv2.imwrite(image_path, canvas)

    compact = locate_ui_element(image_path, "search_box", debug=True)
    assert compact["element"] == "search_box"
    assert abs(compact["x"] - 500) < 80
    assert abs(compact["y"] - 255) < 60
    assert compact["confidence"] >= 0.5

    full = detect_ui_elements(image_path, debug=False)
    assert full["local_only"] is True
    assert full["protected_screenshot"].endswith("_protected.png")
    assert any(item["element"] == "search_button" for item in full["elements"])

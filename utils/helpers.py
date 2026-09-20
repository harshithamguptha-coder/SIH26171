"""
utils/helpers.py
================
Helper utility functions for SIH26171 on-device browser agent.
Contains path management, visual annotation, and logging utilities.
"""

import os
from datetime import datetime
import cv2
import numpy as np


def get_project_root() -> str:
    """Returns the absolute path to the project root folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)


def get_screenshots_dir() -> str:
    """
    Returns the absolute path to the screenshots folder.
    Creates the directory if it does not already exist.
    """
    screenshots_dir = os.path.join(get_project_root(), "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    return screenshots_dir


def generate_screenshot_path(prefix: str = "shot") -> str:
    """
    Generates a unique timestamped file path for saving screenshots locally.
    Example output: screenshots/shot_20260920_113045.png
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    return os.path.join(get_screenshots_dir(), filename)


def draw_bounding_boxes(image_path: str, detections: list, output_path: str = None) -> str:
    """
    Draws rectangular boxes and text labels over an image for all detected visual UI elements.
    
    Parameters:
        image_path (str): Path to the original screenshot.
        detections (list): List of dicts, each containing:
                           {'text': str, 'box': [x, y, w, h], 'confidence': float}
        output_path (str, optional): Destination file path. If None, appends '_annotated'.
        
    Returns:
        str: Path to the annotated image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Read image using OpenCV (BGR format)
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not decode image at {image_path}")

    # Draw each detection box
    for item in detections:
        x, y, w, h = item["box"]
        label = item.get("text", "")
        
        # Draw bounding rectangle (Cyan color in BGR: [255, 200, 0])
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 200, 0), 2)
        
        # Display label if present
        if label:
            # Shorten label if too long for clean display
            display_label = label[:20]
            cv2.putText(
                image,
                display_label,
                (x, max(15, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )

    # Determine destination
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_annotated{ext}"

    cv2.imwrite(output_path, image)
    return output_path


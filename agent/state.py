"""
agent/state.py
==============
Structured screen and browser state representation for SIH26171 Level 2.
Captures on-device visual perceptions, privacy metrics, detected UI elements,
and authentication landmarks without sending any data to the cloud.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class UIElement:
    """Represents an individual detected interactive UI element on the screen."""
    element_type: str
    text: str
    x: int
    y: int
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    method: str = "visual_perception"
    box: List[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.element_type,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": round(float(self.confidence), 3),
            "method": self.method,
            "box": self.box or [self.x, self.y, self.width, self.height],
        }


@dataclass
class ScreenState:
    """
    Structured snapshot of the browser and visual screen state.
    Maintains 100% on-device perception findings and privacy auditing info.
    """
    url: str = ""
    title: str = ""
    page: str = "Unknown"
    raw_screenshot: str = ""
    protected_screenshot: str = ""
    annotated_screenshot: Optional[str] = None
    elements: List[UIElement] = field(default_factory=list)
    text_tokens: List[dict[str, Any]] = field(default_factory=list)
    sensitive_items_masked: int = 0
    sensitive_categories: List[str] = field(default_factory=list)
    is_auth_page: bool = False
    auth_indicators: List[str] = field(default_factory=list)
    uncertain: bool = False
    uncertainty_reason: Optional[str] = None

    def find_element(self, target: str, min_confidence: float = 0.40) -> Optional[UIElement]:
        """
        Locates a target UI element by name, semantic type, or text match.
        Returns the best matching UIElement or None if uncertain.
        """
        target_lower = target.strip().lower()
        if not target_lower:
            return None

        # 1. Direct type or text equality
        for elem in self.elements:
            elem_type = elem.element_type.lower().strip()
            elem_text = elem.text.lower().strip()
            if (elem_type and target_lower == elem_type) or (elem_text and target_lower == elem_text):
                if elem.confidence >= min_confidence:
                    return elem

        # 2. Substring containment
        for elem in self.elements:
            elem_type = elem.element_type.lower().strip()
            elem_text = elem.text.lower().strip()
            if (elem_type and target_lower in elem_type) or (elem_text and (target_lower in elem_text or elem_text in target_lower)):
                if elem.confidence >= min_confidence:
                    return elem

        # 3. Search in OCR tokens
        for token in self.text_tokens:
            t_text = token.get("text", "").lower()
            if target_lower == t_text or (len(target_lower) > 3 and target_lower in t_text):
                conf = float(token.get("confidence", 0.7))
                if conf >= min_confidence:
                    return UIElement(
                        element_type="text_element",
                        text=token.get("text", ""),
                        x=token.get("x", 0) + token.get("width", 0) // 2,
                        y=token.get("y", 0) + token.get("height", 0) // 2,
                        width=token.get("width", 0),
                        height=token.get("height", 0),
                        confidence=conf,
                        method="visual_ocr_token_match",
                        box=[token.get("x", 0), token.get("y", 0), token.get("width", 0), token.get("height", 0)],
                    )

        return None

    def has_text(self, query: str) -> bool:
        """Checks if a given query phrase is visible in the extracted screen text."""
        query_lower = query.strip().lower()
        if not query_lower:
            return False

        # Check in title
        if query_lower in self.title.lower():
            return True

        # Check in elements
        for elem in self.elements:
            if query_lower in elem.text.lower():
                return True

        # Check in tokens
        full_text = " ".join(token.get("text", "") for token in self.text_tokens).lower()
        return query_lower in full_text

    def to_dict(self) -> dict[str, Any]:
        """Converts ScreenState to JSON-serializable dictionary format."""
        return {
            "page": self.page,
            "url": self.url,
            "title": self.title,
            "elements": [elem.to_dict() for elem in self.elements],
            "sensitive_items_masked": self.sensitive_items_masked,
            "sensitive_categories": self.sensitive_categories,
            "is_auth_page": self.is_auth_page,
            "auth_indicators": self.auth_indicators,
            "uncertain": self.uncertain,
            "uncertainty_reason": self.uncertainty_reason,
            "protected_screenshot": self.protected_screenshot,
        }

    def to_json(self, indent: int = 2) -> str:
        """Returns pretty-printed JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


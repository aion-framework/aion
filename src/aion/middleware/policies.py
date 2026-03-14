"""
Input/Output safety middleware for the Aion Framework.

Pipeline that scrubs PII before data hits the LLM and validates
output safety before returning to the user.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod


class SafetyViolationError(Exception):
    """Raised when output fails a safety policy (e.g. toxicity check)."""

    def __init__(self, message: str, policy_name: str = "") -> None:
        self.policy_name = policy_name
        super().__init__(message)


class BasePolicy(ABC):
    """Interface for pre-processing prompts and post-processing responses."""

    @abstractmethod
    def pre_process(self, prompt: str) -> str:
        """Transform input before it reaches the LLM. Default: return as-is."""
        ...

    @abstractmethod
    def post_process(self, response: str) -> str:
        """Transform or validate output before returning to the user. May raise SafetyViolationError."""
        ...


class PIIScrubberPolicy(BasePolicy):
    """
    Regex-based scrubber for PII. Replaces SSNs and emails with [REDACTED_PII].
    """

    # SSN: XXX-XX-XXXX
    _SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    # Common email pattern
    _EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    _REPLACEMENT = "[REDACTED_PII]"

    def pre_process(self, prompt: str) -> str:
        s = self._SSN_PATTERN.sub(self._REPLACEMENT, prompt)
        s = self._EMAIL_PATTERN.sub(self._REPLACEMENT, s)
        return s

    def post_process(self, response: str) -> str:
        s = self._SSN_PATTERN.sub(self._REPLACEMENT, response)
        s = self._EMAIL_PATTERN.sub(self._REPLACEMENT, s)
        return s


class ToxicityValidatorPolicy(BasePolicy):
    """
    Mock validator that raises SafetyViolationError if output contains
    restricted words (e.g. placeholder "confidential_leak").
    """

    RESTRICTED_WORDS = frozenset({"confidential_leak", "internal_only"})

    def pre_process(self, prompt: str) -> str:
        return prompt

    def post_process(self, response: str) -> str:
        lower = response.lower()
        for word in self.RESTRICTED_WORDS:
            if word in lower:
                raise SafetyViolationError(
                    f"Output contained restricted term: {word!r}",
                    policy_name="ToxicityValidatorPolicy",
                )
        return response

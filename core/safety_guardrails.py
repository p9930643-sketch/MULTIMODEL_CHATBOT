import re
import os
from typing import Tuple, Optional
from core.prompt_templates import CRISIS_RESPONSE_TEXT

# Regex patterns indicating crisis, self-harm, or severe danger
CRISIS_PATTERNS = [
    r"\b(suicid(e|al)|kill\s+myself|end\s+my\s+life|want\s+to\s+die|hang\s+myself)\b",
    r"\b(cut\s+myself|self[-\s]?harm|slit\s+my\s+wrist|take\s+all\s+my\s+pills)\b",
    r"\b(don'?t\s+want\s+to\s+live\s+anymore|better\s+off\s+dead|no\s+reason\s+to\s+live)\b",
    r"\b(how\s+to\s+(overdose|hang\s+myself|commit\s+suicide))\b",
]

# Patterns for prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|jailbreak)",
    r"reveal\s+(your\s+)?(system\s+prompt|internal\s+instructions|api\s+key|secret)",
    r"override\s+safety\s+(filters|protocols|guidelines)",
    r"act\s+as\s+an\s+unfiltered\s+ai",
]

class SafetyGuardrails:
    @staticmethod
    def detect_crisis(text: str) -> Tuple[bool, Optional[str]]:
        """
        Scans input for crisis, self-harm, or suicide intent.
        Returns (is_crisis, response_text).
        """
        if not text:
            return False, None

        normalized = text.lower()
        for pattern in CRISIS_PATTERNS:
            if re.search(pattern, normalized):
                return True, CRISIS_RESPONSE_TEXT

        return False, None

    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        """
        Sanitizes text extracted from external files to prevent prompt injection.
        Disarms typical instruction-override triggers.
        """
        if not text:
            return ""

        # Normalize potential escape characters
        sanitized = text.replace("\x00", "")
        # Neutralize markdown comment tricks or role spoofing
        sanitized = re.sub(r"(?i)system:\s*", "[document text]: ", sanitized)
        return sanitized

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        """
        Returns True if prompt injection indicators are found.
        """
        if not text:
            return False
        normalized = text.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, normalized):
                return True
        return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Ensures filename is safe against directory traversal.
        """
        base = os.path.basename(filename)
        # Keep only alphanumeric, underscores, hyphens, and periods
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
        # Ensure it doesn't start with period
        if cleaned.startswith("."):
            cleaned = "file_" + cleaned
        return cleaned or "uploaded_file"

    @staticmethod
    def append_medical_disclaimer(reply: str, mentions_health: bool = False) -> str:
        """
        Appends gentle medical disclaimer if health/mental-health themes are present.
        """
        disclaimer = "\n\n*(Note: I am an AI companion, not a licensed medical professional or therapist. Please consult a qualified healthcare provider for clinical medical or psychological advice.)*"
        if mentions_health and disclaimer not in reply:
            return reply + disclaimer
        return reply

safety_guardrails = SafetyGuardrails()

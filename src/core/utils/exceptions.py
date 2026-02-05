"""
Custom exception classes for the Signature Semantic Decoder.
"""

from typing import Any, Dict, Optional


class SignatureDecoderError(Exception):
    """Base exception for all signature decoder errors."""

    default_message = "Signature decoder error"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        resolved_message = message or self.default_message
        super().__init__(resolved_message)
        self.message = resolved_message
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} | context={self.context}"
        return self.message


class ValidationError(SignatureDecoderError):
    """Raised when input validation fails."""

    default_message = "Input validation failed"


class SchemaError(SignatureDecoderError):
    """Raised when EIP-712 schema validation fails."""

    default_message = "EIP-712 schema validation failed"


class ParsingError(SignatureDecoderError):
    """Raised when parsing fails."""

    default_message = "Parsing failed"


class ClassificationError(SignatureDecoderError):
    """Raised when classification fails."""

    default_message = "Classification failed"


class InterpretationError(SignatureDecoderError):
    """Raised when semantic interpretation fails."""

    default_message = "Interpretation failed"


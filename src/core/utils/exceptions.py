"""
Custom exception classes for the Signature Semantic Decoder.
"""


class SignatureDecoderError(Exception):
    """Base exception for all signature decoder errors."""
    pass


class ValidationError(SignatureDecoderError):
    """Raised when input validation fails."""
    pass


class SchemaError(SignatureDecoderError):
    """Raised when EIP-712 schema validation fails."""
    pass


class ParsingError(SignatureDecoderError):
    """Raised when parsing fails."""
    pass


class ClassificationError(SignatureDecoderError):
    """Raised when classification fails."""
    pass


class InterpretationError(SignatureDecoderError):
    """Raised when semantic interpretation fails."""
    pass


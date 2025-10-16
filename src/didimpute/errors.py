from __future__ import annotations


class ValidationError(Exception):
    """Raised when input data or configuration fails validation."""


class EstimationError(Exception):
    """Raised when estimation or prediction cannot proceed."""

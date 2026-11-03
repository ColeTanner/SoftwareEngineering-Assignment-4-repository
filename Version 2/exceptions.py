class PRSError(Exception):
    """Base domain exception for the Patient Record System."""
    pass

class ValidationError(PRSError):
    """Raised when user input violates format, character, or length rules."""
    pass

class PatientNotFoundError(PRSError):
    """Raised when a patient ID does not exist in storage."""
    pass

class UnauthorizedAccessError(PRSError):
    """Raised when a staff user lacks role permission for an operation."""
    pass

class DuplicateRecordError(PRSError):
    """Raised when an identifier or unique constraint is violated."""
    pass

class DatabaseOperationError(PRSError):
    """Raised when a database transaction or connection fails."""
    pass
"""Custom exceptions for the MetroGo fleet dispatcher."""


class MetroGoException(Exception):
    """Base exception class for all MetroGo runtime errors."""
    pass


class VehicleValidationError(MetroGoException):
    """Raised when vehicle data fails validation."""
    pass


class InvalidLocationError(MetroGoException):
    """Raised when a location is outside valid coordinate bounds."""
    pass


class DispatchFailureException(MetroGoException):
    """Raised when no viable vehicle can satisfy a dispatch request."""
    pass


class VehicleNotFoundError(MetroGoException):
    """Raised when a requested vehicle VIN is not in the fleet."""
    pass


class FareCalculationError(MetroGoException):
    """Raised when a vehicle base rate is invalid."""
    pass


class BatteryDepletedError(MetroGoException):
    """Raised when an electric vehicle cannot satisfy a battery requirement."""
    pass

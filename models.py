""" OOP models for the MetroGo fleet dispatcher."""

from abc import ABC, abstractmethod
from math import sqrt

from helpers import (
    DispatchFailureException,
    FareCalculationError,
    InvalidLocationError,
    VehicleNotFoundError,
    VehicleValidationError,
)


class Vehicle(ABC):
    """Abstract base class shared by every MetroGo vehicle."""

    def __init__(
        self,
        vin: str,
        model_name: str,
        base_rate: float,
        current_location: tuple,
    ):
        self.vin = vin
        self.model_name = model_name
        self.base_rate = base_rate
        self.current_location = current_location

    @property
    def vin(self) -> str:
        return self._vin

    @vin.setter
    def vin(self, value: str):
        if not isinstance(value, str) or len(value) != 17 or not value.isalnum():
            raise VehicleValidationError(
                f"Invalid VIN: '{value}'. VIN must be exactly 17 alphanumeric characters."
            )
        self._vin = value.upper()

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise VehicleValidationError("Model name must be a non-empty string.")
        self._model_name = value.strip()

    @property
    def base_rate(self) -> float:
        return self._base_rate

    @base_rate.setter
    def base_rate(self, value: float):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise FareCalculationError(
                "Base rate must be strictly positive (greater than 0.0)."
            )
        self._base_rate = float(value)

    @property
    def current_location(self) -> tuple:
        return self._current_location

    @current_location.setter
    def current_location(self, value: tuple):
        if not isinstance(value, tuple) or len(value) != 2:
            raise InvalidLocationError(
                "Location must be a tuple containing (latitude, longitude)."
            )

        lat, lon = value
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise InvalidLocationError("Latitude and longitude must be numbers.")

        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            raise InvalidLocationError(
                f"Latitude ({lat}) or Longitude ({lon}) out of bounds."
            )

        self._current_location = (float(lat), float(lon))

    @abstractmethod
    def calculate_fare(self, distance_miles: float, surge_multiplier: float) -> float:
        """Calculate a fare using the vehicle's pricing strategy."""
        pass

    @abstractmethod
    def verify_dispatch_viability(self, trip_requirements: dict) -> bool:
        """Return whether this vehicle can satisfy the request."""
        pass


class EconomyVehicle(Vehicle):
    """Standard economy vehicle."""

    def calculate_fare(self, distance_miles: float, surge_multiplier: float) -> float:
        return round(distance_miles * self.base_rate * surge_multiplier, 2)

    def verify_dispatch_viability(self, trip_requirements: dict) -> bool:
        return True


class PremiumVehicle(Vehicle):
    """Premium vehicle with luxury markup and booking fee."""

    LUXURY_COEFFICIENT = 1.5
    BOOKING_FEE = 15.00

    def calculate_fare(self, distance_miles: float, surge_multiplier: float) -> float:
        base_calculation = (
            distance_miles
            * self.base_rate
            * surge_multiplier
            * self.LUXURY_COEFFICIENT
        )
        return round(base_calculation + self.BOOKING_FEE, 2)

    def verify_dispatch_viability(self, trip_requirements: dict) -> bool:
        return trip_requirements.get("requires_premium", False)


class ElectricVehicle(Vehicle):
    """Electric vehicle with battery validation and a green fare discount."""

    def __init__(
        self,
        vin: str,
        model_name: str,
        base_rate: float,
        current_location: tuple,
        battery_level: int = 100,
    ):
        super().__init__(vin, model_name, base_rate, current_location)
        self.battery_level = battery_level

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @battery_level.setter
    def battery_level(self, value: int):
        if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 100):
            raise VehicleValidationError(
                "Battery level must be an integer between 0 and 100."
            )
        self._battery_level = value

    def calculate_fare(self, distance_miles: float, surge_multiplier: float) -> float:
        return round(distance_miles * self.base_rate * surge_multiplier * 0.9, 2)

    def verify_dispatch_viability(self, trip_requirements: dict) -> bool:
        min_charge = trip_requirements.get("min_battery", 20)
        return self.battery_level >= min_charge


class Fleet:
    """Composition-based manager for the active MetroGo vehicle fleet."""

    def __init__(self):
        self._vehicles = []

    def register_vehicle(self, vehicle: Vehicle) -> None:
        try:
            vin = vehicle.vin
            vehicle.calculate_fare
            vehicle.verify_dispatch_viability
        except AttributeError as exc:
            raise VehicleValidationError(
                "Only valid Vehicle objects can be registered."
            ) from exc

        if any(existing.vin == vin for existing in self._vehicles):
            raise VehicleValidationError(
                f"Vehicle with VIN '{vin}' is already registered."
            )

        self._vehicles.append(vehicle)

    def remove_vehicle(self, vin: str) -> None:
        for index, vehicle in enumerate(self._vehicles):
            if vehicle.vin == vin.upper():
                self._vehicles.pop(index)
                return

        raise VehicleNotFoundError(f"No vehicle found with VIN '{vin}'.")

    def list_vehicles(self) -> tuple:
        """Return a read-only snapshot of the active vehicles."""
        return tuple(self._vehicles)

    @staticmethod
    def _distance(point_a: tuple, point_b: tuple) -> float:
        lat1, lon1 = point_a
        lat2, lon2 = point_b
        return sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)

    def query_dispatchable_fleet(self, trip_requirements: dict) -> list:
        """Return viable vehicles ordered by proximity to the pickup location."""
        pickup = trip_requirements.get("pickup_location")
        if pickup is None:
            pickup = trip_requirements.get("origin")

        if pickup is not None:
            if not isinstance(pickup, tuple) or len(pickup) != 2:
                raise InvalidLocationError(
                    "pickup_location must be a (latitude, longitude) tuple."
                )

        max_distance = trip_requirements.get("max_distance", float("inf"))
        candidates = []

        for vehicle in self._vehicles:
            distance = (
                self._distance(vehicle.current_location, pickup)
                if pickup is not None
                else 0.0
            )

            if distance > max_distance:
                continue

            if vehicle.verify_dispatch_viability(trip_requirements):
                candidates.append((distance, vehicle))

        candidates.sort(key=lambda item: item[0])
        return [vehicle for _, vehicle in candidates]

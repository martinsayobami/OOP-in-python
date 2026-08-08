"""Command-line entry point for the MetroGo Fleet Dispatcher."""

from helpers import DispatchFailureException, MetroGoException
from models import EconomyVehicle, ElectricVehicle, Fleet, PremiumVehicle


def main_menu():
    print("\n--- MetroGo Corporate Fleet Management Interface ---")
    print("1. Register a New Fleet Vehicle")
    print("2. List All Active Fleet Vehicles")
    print("3. Execute Polymorphic Dispatch Request")
    print("4. Remove a Vehicle")
    print("5. Exit")


def _read_location(label: str) -> tuple:
    latitude = float(input(f"{label} latitude: "))
    longitude = float(input(f"{label} longitude: "))
    return (latitude, longitude)


def _register_vehicle(fleet: Fleet):
    print("\n--- Register Vehicle ---")
    vehicle_type = input(
        "Vehicle type [economy/premium/electric]: "
    ).strip().lower()

    vin = input("VIN (17 alphanumeric characters): ").strip()
    model_name = input("Model name: ").strip()
    base_rate = float(input("Base rate: "))
    location = _read_location("Current location")

    if vehicle_type == "economy":
        vehicle = EconomyVehicle(vin, model_name, base_rate, location)
    elif vehicle_type == "premium":
        vehicle = PremiumVehicle(vin, model_name, base_rate, location)
    elif vehicle_type == "electric":
        battery = int(input("Battery level (0-100): "))
        vehicle = ElectricVehicle(
            vin, model_name, base_rate, location, battery
        )
    else:
        print("Unknown vehicle type.")
        return

    fleet.register_vehicle(vehicle)
    print(f"{model_name} registered successfully.")


def _list_vehicles(fleet: Fleet):
    vehicles = fleet.list_vehicles()

    if not vehicles:
        print("\nNo active vehicles in the fleet.")
        return

    print("\n--- Active Fleet Vehicles ---")
    print(f"{'VIN':<20}{'Model':<22}{'Base Rate':<12}{'Location':<22}")
    print("-" * 76)

    for vehicle in vehicles:
        print(
            f"{vehicle.vin:<20}"
            f"{vehicle.model_name:<22}"
            f"{vehicle.base_rate:<12.2f}"
            f"{str(vehicle.current_location):<22}"
        )


def _dispatch_vehicle(fleet: Fleet):
    print("\n--- Dispatch Request ---")
    pickup = _read_location("Pickup")
    trip_distance = float(input("Trip distance: "))
    surge = float(input("Surge multiplier: "))

    requires_premium = (
        input("Requires premium vehicle? [y/n]: ").strip().lower() == "y"
    )
    min_battery = int(
        input("Minimum battery required [default 20]: ") or "20"
    )
    max_distance = float(
        input("Maximum pickup distance [default unlimited]: ") or "inf"
    )

    requirements = {
        "pickup_location": pickup,
        "requires_premium": requires_premium,
        "min_battery": min_battery,
        "max_distance": max_distance,
    }

    candidates = fleet.query_dispatchable_fleet(requirements)

    if not candidates:
        raise DispatchFailureException(
            "No viable vehicle was found for this dispatch request."
        )

    vehicle = candidates[0]
    fare = vehicle.calculate_fare(trip_distance, surge)

    print("\n--- Dispatch Result ---")
    print(f"Assigned vehicle: {vehicle.model_name}")
    print(f"VIN: {vehicle.vin}")
    print(f"Fare: {fare:.2f}")
    print("Dispatch approved.")


def _remove_vehicle(fleet: Fleet):
    vin = input("Enter VIN to remove: ").strip()
    fleet.remove_vehicle(vin)
    print("Vehicle removed successfully.")


def run():
    fleet = Fleet()

    # Seed records from the assignment skeleton so the CLI can be tested immediately.
    fleet.register_vehicle(
        EconomyVehicle(
            "11111111111111111", "Toyota Camry", 2.50, (6.52, 3.37)
        )
    )
    fleet.register_vehicle(
        PremiumVehicle(
            "22222222222222222", "Mercedes S-Class", 5.00, (6.55, 3.39)
        )
    )
    fleet.register_vehicle(
        ElectricVehicle(
            "33333333333333333", "Tesla Model Y", 3.00, (6.50, 3.35), 85
        )
    )

    while True:
        main_menu()
        choice = input("Enter option [1-5]: ").strip()

        try:
            if choice == "1":
                _register_vehicle(fleet)
            elif choice == "2":
                _list_vehicles(fleet)
            elif choice == "3":
                _dispatch_vehicle(fleet)
            elif choice == "4":
                _remove_vehicle(fleet)
            elif choice == "5":
                print("Exiting MetroGo. System Offline.")
                break
            else:
                print("Invalid option selected. Please select a valid choice.")

        except MetroGoException as exc:
            print(f"\n[EXECUTION ERROR] {exc}")
        except (ValueError, TypeError) as exc:
            print(f"\n[INPUT ERROR] Please enter a valid value: {exc}")
        except Exception as exc:
            print(f"\n[CRITICAL ERROR] Unexpected failure: {exc}")


if __name__ == "__main__":
    run()

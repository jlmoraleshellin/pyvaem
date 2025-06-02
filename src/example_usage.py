"""Example usage of the PyVaem API.

This module demonstrates the key functionality of the PyVaem API for controlling
Festo VAEM valve modules. The examples show how to:
1. Configure and connect to a VAEM device
2. Configure valve settings
3. Control valve selection and operation
4. Read device status

Note: Replace the VaemConfig parameters with your device's actual values.
"""

import time

from pyvaem import VaemConfig, VaemDriver, ValveSettings


def configure_valves_example(vaem: VaemDriver):
    """Demonstrates different ways to configure valve settings."""
    # Configure using a dictionary
    settings_dict = {
        "NominalVoltage": 24000,
        "ResponseTime": 500,
        "TimeDelay": 0,
        "PickUpTime": 125,
        "InrushCurrent": 300,
        "HitNHold": 100,
        "HoldingCurrent": 100,
    }
    vaem.set_valve_settings(1, settings_dict)  # Configure valve 1

    # Configure using a partial dictionary
    partial_settings_dict = {
        "NominalVoltage": 24000,
        "ResponseTime": 500,
        # Rest of the settings will use defaults
    }
    vaem.set_valve_settings(2, partial_settings_dict)  # Configure valve 2

    # Configure using ValveSettings object
    settings_obj = ValveSettings(
        NominalVoltage=24000,
        ResponseTime=500,
        TimeDelay=0,
        PickUpTime=125,
        InrushCurrent=300,
        HitNHold=100,
        HoldingCurrent=100,
    )
    vaem.set_valve_settings(3, settings_obj)  # Configure valve 3

    # Configure with partial settings (others use defaults)
    partial_settings = ValveSettings(
        NominalVoltage=24000,
        TimeDelay=0,
        PickUpTime=125,
        HitNHold=100,
        HoldingCurrent=100,
        # ResponseTime will default to 500
        # InrushCurrent will default to 300
    )
    vaem.set_valve_settings(4, partial_settings)  # Configure valve 4

    # Save settings to VAEM device memory (optional)
    vaem.save_settings()


def valve_control_example(vaem: VaemDriver):
    """Demonstrates valve selection and control operations."""
    # Select multiple valves at once
    vaem.select_valves([1, 1, 1, 0, 0, 0, 0, 0])  # Select valves 1, 2 and 3

    # Read device status
    print("Device status:", vaem.get_status())
    print("Selected valves:", vaem.read_valves_state())

    # Control selected valves
    vaem.open_valves()
    time.sleep(2)
    # ... valves are open ...
    vaem.close_valves()

    # Individual valve selection
    vaem.deselect_all_valves()
    vaem.select_valve(1)  # Select just valve 1
    print("Status after selecting valve 1:", vaem.get_status())

    vaem.open_valves()
    time.sleep(2)
    # ... valve 1 is open ...
    vaem.close_valves()


def main():
    """Main example showing VAEM device usage."""
    # Configure connection to VAEM device
    config = VaemConfig(
        ip="192.168.1.100",  # Replace with actual device IP
        port=502,  # Default VAEM port
        slave_id=1,  # Replace with actual slave ID
    )

    try:
        # Initialize VAEM driver
        vaem = VaemDriver(config)

        # Run example operations
        configure_valves_example(vaem)
        valve_control_example(vaem)

    except ConnectionError as e:
        print(e)


if __name__ == "__main__":
    main()

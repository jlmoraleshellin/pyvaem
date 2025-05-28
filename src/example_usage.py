import time
from logging import Logger

from pyvaem import VaemConfig, VaemDriver, ValveSettings

if __name__ == "__main__":
    vaem_config = VaemConfig("192.168.8.118", 502, 0)

    try:
        vaem = VaemDriver(vaem_config, logger=Logger("vaem_logger"))
    except Exception as e:
        print(e)

    def example():
        # Example usage
        # Set per-valve settings using a dictionary
        for valve in range(1, 9):
            vaem.set_valve_settings(
                valve,
                {
                    "NominalVoltage": 24000,
                    "ResponseTime": 500,
                    "TimeDelay": 0,
                    "PickUpTime": 125,
                    "InrushCurrent": 300,
                    "HitNHold": 100,
                    "HoldingCurrent": 100,
                },
            )

        # Or using a ValveSettings object
        for valve in range(1, 9):
            vaem.set_valve_settings(
                valve,
                ValveSettings(
                    NominalVoltage=24000,
                    ResponseTime=500,
                    TimeDelay=0,
                    PickUpTime=125,
                    InrushCurrent=300,
                    HitNHold=100,
                    HoldingCurrent=100,
                ),
            )

        # If not specified, setting will be set as default
        # (same will happen if a dict is used)
        for valve in range(1, 9):
            vaem.set_valve_settings(
                valve,
                ValveSettings(
                    NominalVoltage=24000,
                    # ResponseTime will be 500,
                    TimeDelay=0,
                    PickUpTime=125,
                    # InrushCurrent will be 300,
                    HitNHold=100,
                    HoldingCurrent=100,
                ),
            )

        # Optional: Call save_settings to save settings to the memory of the VAEM
        vaem.save_settings()

        # Select multiple valves in one call
        vaem.select_valves([1, 1, 1, 0, 0, 0, 0, 0])  # Select valves 1, 2 and 3

        # Read the device status
        # Get status returns the status of the device including selected valves
        print(vaem.get_status())
        # Read valves state returns just the selected states as a tuple
        print(vaem.read_valves_state())

        vaem.open_valves()  # Open selected valves
        time.sleep(3)
        vaem.close_valves()  # Close all valves

        # Deselect all valves
        vaem.deselect_all_valves()

        # Or select valves one by one
        vaem.select_valve(1)
        print(vaem.get_status())

        vaem.open_valves()  # Open selected valves
        time.sleep(3)
        vaem.close_valves()  # Close all valves

    example()

import logging
import time
from pyvaem.VaemDriver import vaemDriver
from pyvaem.vaemHelper import ValveSettings
from pyvaem.dataTypes import VaemConfig


if __name__ == "__main__":
    vaemConfig = VaemConfig("192.168.8.118", 502, 0)

    try:
        vaem = vaemDriver(vaemConfig, logger=logging.Logger("vaem_logger"))
    except Exception as e:
        print(e)

    def func():
        # Example usage
        # Set per-valve settings using a dictionary
        for valve in range(1, 9):
            vaem.set_multiple_valve_settings(
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
            vaem.set_multiple_valve_settings(
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
        
        # Call save_settings to apply the changes
        vaem.save_settings()

        # Select multiple valves in one call
        vaem.select_valves([1, 1, 1, 0, 0, 0, 0, 0])  # Select valves 1, 2 and 3

        # Read the device status
        # Get status returns the status of the device
        # and which valves are selected in a dict format
        print(vaem.get_status())
        # Read valves state returns just the states (selected or not) as a list
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

    func()

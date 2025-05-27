import logging
import time

from pymodbus.client import ModbusTcpClient as TcpClient

from pyvaem.dataTypes import VaemConfig
from pyvaem.vaemHelper import (
    VaemAccess,
    VaemControlWords,
    VaemDataType,
    VaemIndex,
    VaemOperatingMode,
    VaemRegisters,
    ValveSettings,
    VaemRanges,
    create_setting_registers,
    create_select_valve_registers,
    create_controlword_registers,
    parse_statusword,
    vaemValveIndex,
)

readParam = {
    "address": 0,
    "length": 0x07,
}

writeParam = {
    "address": 0,
    "length": 0x07,
}

error_codes = {
    0: "Ready for operation, no error",
    34: "Invalid index",
    35: "Invalid subindex",
    36: "Read request cannot be processed",
    37: "Write request cannot be processed",
    41: "Specified value falls below the minimum value",
    42: "The specified value exceeds the maximum value",
    43: "Incorrect transfer value",
    44: "Data type incorrect",
    93: "General syntax error",
    94: "Syntax error index (variable x)",
    95: "Syntax error subindex (variable y)",
    96: "Syntax error value",
    97: "Command execution aborted",
}


def handle_error_response(func):
    def wrapper(self: "vaemDriver", *args, **kwargs):
        if not self._vaem_connected:
            self._log.warning("No VAEM Connected")
            return

        result: VaemRegisters = func(self, *args, **kwargs)

        if result is None:
            return result

        error = result.errorRet
        if error != 0:
            self._log.error(f"{error_codes[error]}")
            self.clear_error()

        return result

    return wrapper


class vaemDriver:
    def __init__(self, vaemConfig: VaemConfig, logger=logging.getLogger("vaem")):
        self._config = vaemConfig
        self._log = logger
        self._vaem_connected = False

        self.client = TcpClient(host=self._config.ip, port=self._config.port)

        for _ in range(2):
            if self.client.connect():
                break
            else:
                self._log.warning(f"Failed to connect VAEM. Reconnecting attempt: {_}")
            if _ == 1:
                self._log.error(f"Could not connect to VAEM: {self._config}")
                raise ConnectionError(f"Could not connect to VAEM: {self._config}")

        self._log.info(f"Connected to VAEM : {self._config}")
        self._vaem_connected = True
        self.set_operating_mode(VaemOperatingMode.OpMode1)
        self.clear_error()

    def _read_write_registers(self, writeData: list) -> list:
        try:
            data = self.client.readwrite_registers(
                read_address=readParam["address"],
                read_count=readParam["length"],
                write_address=writeParam["address"],
                values=writeData,
                slave=self._config.slave_id,
            )
            return data.registers
        except Exception as e:
            self._log.error(f"Something went wrong with read opperation VAEM : {e}")
            return []

    def _transfer_vaem_registers(self, vaem_reg: VaemRegisters) -> VaemRegisters:
        """Helper method to handle the common transfer pattern"""
        resp = self._read_write_registers(vaem_reg.to_list())
        return VaemRegisters.from_list(resp)

    @handle_error_response
    def set_operating_mode(self, mode: VaemOperatingMode):
        """Set the operating mode of the VAEM"""
        data = VaemRegisters(
            access=VaemAccess.Write.value,
            dataType=VaemDataType.UINT8.value,
            paramIndex=VaemIndex.OperatingMode.value,
            paramSubIndex=0,
            errorRet=0,
            transferValue=mode.value,
        )
        return self._transfer_vaem_registers(data)

    ### VALVE SELECTION OPERATIONS ###
    @handle_error_response
    def select_valve(self, valve_id: int):
        """Selects one valve in the VAEM.
        According to VAEM Logic all selected valves can be opened

        @param: valve_id - the id of the valve to select from 1 to 8

        raises:
            ValueError - raised if the valve id is not supported
        """
        if valve_id in range(1, 9):
            self._log.error("valve_id must be between 1-8")
            return

        # get currently selected valves
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        resp = self._transfer_vaem_registers(data)

        # select new valve
        data = create_select_valve_registers(
            VaemAccess.Write.value, vaemValveIndex[valve_id] | resp.transferValue
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def deselect_valve(self, valve_id: int) -> dict:
        """Deselects one valve in the VAEM.

        @param: valve_id - the id of the valve to select. valid numbers are from 1 to 8

        raises:
            ValueError - raised if the valve id is not supported
        """
        if valve_id in range(1, 9):
            self._log.error("valve_id must be between 1-8")
            return

        # get currently selected valves
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        resp = self._transfer_vaem_registers(data)

        # deselect new valve
        data = create_select_valve_registers(
            VaemAccess.Write.value, resp.transferValue & (~(vaemValveIndex[valve_id]))
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def select_valves(self, states: list[int]):
        """Select multiple valves at once by specifying states for all valves.
        See documentation on how to open multiple valves.

        Args:
         valve_states:
           list of 8 values (0 or 1) representing valve states from left to right (valve 1 is first element, valve 8 is last)
        """

        # Ensure there are 8 states
        if len(states) != 8:
            self._log.error("Must provide 8 valve states")
            return

        # Reverse the list to match controller's right-to-left bit ordering
        reversed_states = states.copy()
        reversed_states.reverse()
        # Convert the reversed list to a binary string, then to decimal
        binary_string = "".join(str(state) for state in reversed_states)
        decimal_code = int(binary_string, 2)

        # Select valves by directly writing the binary pattern
        data = create_select_valve_registers(VaemAccess.Write.value, decimal_code)
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def select_all_valves(self):
        data = create_select_valve_registers(
            VaemAccess.Write.value, vaemValveIndex["AllValves"]
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def deselect_all_valves(self):
        data = create_select_valve_registers(VaemAccess.Write.value, 0)
        return self._transfer_vaem_registers(data)

    ### VALVE SETTINGS OPERATIONS ###
    @handle_error_response
    def set_valve_setting(self, valve_id: int, setting: VaemIndex, value: int):
        valid_range = VaemRanges.get(setting.name)
        if valid_range is None:
            self._log.error(f"VaemIndex {setting.name} is not a setting")
            return

        if value not in range(*valid_range) and valve_id not in range(1, 9):
            self._log.error(
                f"{setting.name} must be in range {valid_range[0]} - {valid_range[1] - 1} and valve_id -> 1-8"
            )
            return

        data = create_setting_registers(
            setting,
            valve_id - 1,
            VaemAccess.Write.value,
            int(value),
        )
        return self._transfer_vaem_registers(data)

    def set_multiple_valve_settings(
        self, valve_id, settings: ValveSettings | dict[str, int] = None
    ):
        """Configure settings for a specific valve. This method allows setting various
        parameters for a given valve.

        Args:
            valve_id: Valve ID (1-8)
            settings: ValveSettings object, dict of settings, or None for defaults
        """
        if valve_id not in range(1, 9):
            self._log.error("valve_id must be between 1-8")
            return

        # Handle different input types
        if settings is None:
            valve_settings = ValveSettings()
        elif isinstance(settings, dict):
            valve_settings = ValveSettings.from_dict(settings)
        elif isinstance(settings, ValveSettings):
            valve_settings = settings
        else:
            self._log.error(f"Invalid settings type: {type(settings)}")
            return

        for setting, value in valve_settings.to_enum_dict().items():
            self.set_valve_setting(valve_id, setting, value)

    @handle_error_response
    def save_settings(self):
        data = VaemRegisters(
            access=VaemAccess.Write.value,
            dataType=VaemDataType.UINT32.value,
            paramIndex=VaemIndex.SaveParameters.value,
            paramSubIndex=0,
            errorRet=0,
            transferValue=99999,
        )

        return self._transfer_vaem_registers(data)

    @handle_error_response
    def read_valve_setting(self, valve_id, setting: VaemIndex):
        """Read settings for a specific valve."""
        # Check if parameter is actually a setting
        if VaemRanges.get(setting.name) is None:
            self._log.error(f"VaemIndex {setting.name} is not a setting")
            return

        data = create_setting_registers(
            setting,
            valve_id - 1,  # Valve id starts at 0 for settings
            VaemAccess.Read.value,
        )
        return self._transfer_vaem_registers(data)

    def read_all_valve_settings(self, valve_id: int):
        """Read all settings for a specific valve and returns them as a ValveSettings object"""
        if valve_id not in range(1, 9):
            self._log.error("valve_id must be between 1-8")
            return

        settings = {}
        for setting in VaemRanges.keys():
            value = self.read_valve_setting(valve_id, setting)
            if value is not None:
                settings.update(setting, value.transferValue)

        return ValveSettings.from_dict(settings)

    ### VALVE OPERATIONS ###
    @handle_error_response
    def open_valves(self):
        """Start all valves that are selected"""
        self._reset_control_word()

        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.StartValves.value
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def close_valves(self):
        """Close all valves"""
        self._reset_control_word()

        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.StopValves.value
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def clear_error(self):
        """If any error occurs in valve opening, must be cleared with this opperation."""
        self._reset_control_word()

        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.ResetErrors.value
        )
        return self._transfer_vaem_registers(data)

    @handle_error_response
    def _reset_control_word(self):
        """Reset control word"""
        data = create_controlword_registers(VaemAccess.Write.value, 0)
        return self._transfer_vaem_registers(data)

    def read_valves_state(self):
        if not self._vaem_connected:
            self._log.warning("No VAEM Connected!!")
            return None

        # get currently selected valves
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        resp = self._transfer_vaem_registers(data)

        # Convert to binary and ensure it's 8 bits (pad with leading zeros if needed)
        binary_string = format(resp.transferValue, "08b")
        # Convert to list of integers and reverse to match user-expected order
        states = [int(bit) for bit in binary_string]
        states.reverse()

        return states

    @handle_error_response
    def _read_status_word(self):
        """
        Read the statusword
        The status is return as a dictionary with the following keys:
        -> status: 1 if more than 1 valve is active
        -> error: 1 if error in valves is present
        """
        data = VaemRegisters(
            access=VaemAccess.Read.value,
            dataType=VaemDataType.UINT16.value,
            paramIndex=VaemIndex.StatusWord.value,
            paramSubIndex=0,
            errorRet=0,
            transferValue=0,
        )
        return self._transfer_vaem_registers(data)

    def get_status(self):
        """
        Get the status of the VAEM
        The status is returned as a dictionary with the following keys:
        -> status: 1 if more than 1 valve is active
        -> error: 1 if error in valves is present
        """
        return parse_statusword(self._read_status_word().to_list())

    def wait_for_readiness(self, timeout=10.0):
        """
        Wait for the device to be ready with a timeout.
        """
        start_time = time.time()

        while True:
            # Check if timeout has been exceeded
            if time.time() - start_time > timeout:
                self._log.warning(
                    f"Timeout waiting for device readiness after {timeout} seconds"
                )
                return False

            readiness = self.get_status()["Readiness"]
            if readiness == 0:
                time.sleep(0.1)
                print(readiness)
                pass
            else:
                return True

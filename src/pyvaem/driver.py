import logging
import time
from typing import Callable, Concatenate, ParamSpec, TypeVar

from pymodbus.client import ModbusTcpClient as TcpClient

from pyvaem.config import VaemConfig, ValveSettings
from pyvaem.utils import (
    VaemAccess,
    VaemControlWords,
    VaemDataType,
    VaemIndex,
    VaemOperatingMode,
    VaemRegisters,
    create_controlword_registers,
    create_select_valve_registers,
    create_setting_registers,
    error_msgs,
    error_types,
    parse_statusword,
    vaem_parameters,
    vaem_ranges,
    valve_indexes,
)

P = ParamSpec("P")
R = TypeVar("R", bound=VaemRegisters)


def clear_and_raise_error(
    func: Callable[Concatenate["VaemDriver", P], R],
) -> Callable[Concatenate["VaemDriver", P], R]:
    def wrapper(self: "VaemDriver", *args, **kwargs):
        result = func(self, *args, **kwargs)

        def raise_error(error_code: int):
            error = error_types[error_code]
            msg = error_msgs[error_code]
            raise error(msg)

        error = result.errorRet
        if error != 0:
            self.clear_error()
            raise_error(error)

        return result

    return wrapper


class VaemDriver:
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
                raise ConnectionError(f"Could not connect to VAEM: {self._config}")

        self._log.info(f"Connected to VAEM : {self._config}")
        self._vaem_connected = True
        self.set_operating_mode(VaemOperatingMode.OpMode1)
        self.clear_error()

    def _transfer_vaem_registers(self, vaem_reg: VaemRegisters) -> VaemRegisters:
        """Method to handle the common transfer pattern"""

        def _read_write_registers() -> list:
            read_param = {"address": 0, "length": 0x07}
            write_param = {"address": 0, "length": 0x07}
            try:
                data = self.client.readwrite_registers(
                    read_address=read_param["address"],
                    read_count=read_param["length"],
                    write_address=write_param["address"],
                    values=vaem_reg.to_list(),
                    slave=self._config.slave_id,
                )
                return data.registers
            except Exception as e:
                self._log.error(f"Something went wrong with read opperation VAEM : {e}")
                raise

        return VaemRegisters.from_list(_read_write_registers())

    @clear_and_raise_error
    def set_operating_mode(self, mode: VaemOperatingMode) -> VaemRegisters:
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
    @clear_and_raise_error
    def select_valve(self, valve_id: int) -> VaemRegisters:
        """Selects one valve in the VAEM.
        According to VAEM Logic all selected valves can be opened

        @param: valve_id - the id of the valve to select from 1 to 8

        raises:
            ValueError - raised if the valve id is not supported
        """
        if valve_id in range(1, 9):
            raise ValueError("Valve_id must be between 1-8")

        # get currently selected valves
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        resp = self._transfer_vaem_registers(data)

        # select new valve
        data = create_select_valve_registers(
            VaemAccess.Write.value, valve_indexes[valve_id] | resp.transferValue
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def deselect_valve(self, valve_id: int) -> VaemRegisters:
        """Deselects one valve in the VAEM.

        @param: valve_id - the id of the valve to select. valid numbers are from 1 to 8

        raises:
            ValueError - raised if the valve id is not supported
        """
        if valve_id in range(1, 9):
            raise ValueError("Valve_id must be between 1-8")

        # get currently selected valves
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        resp = self._transfer_vaem_registers(data)

        # deselect new valve
        data = create_select_valve_registers(
            VaemAccess.Write.value, resp.transferValue & (~(valve_indexes[valve_id]))
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def select_valves(self, states: list[int]) -> VaemRegisters:
        """Select multiple valves at once by specifying states for all valves.
        See documentation on how to open multiple valves.

        Args:
         valve_states:
           list of 8 values (0 or 1) representing valve states from left to right (valve 1 is first element, valve 8 is last)
        """
        if len(states) != 8:
            raise ValueError("Must provide 8 valve states")

        def convert_to_binary_string():
            reversed_states = reversed(states)
            return "".join(str(state) for state in reversed_states)

        decimal_code = int(convert_to_binary_string(), 2)
        data = create_select_valve_registers(VaemAccess.Write.value, decimal_code)
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def select_all_valves(self) -> VaemRegisters:
        data = create_select_valve_registers(
            VaemAccess.Write.value, valve_indexes["AllValves"]
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def deselect_all_valves(self) -> VaemRegisters:
        data = create_select_valve_registers(VaemAccess.Write.value, 0)
        return self._transfer_vaem_registers(data)

    ### VALVE SETTINGS OPERATIONS ###
    @clear_and_raise_error
    def _set_valve_setting(
        self, valve_id: int, setting: VaemIndex, value: int
    ) -> VaemRegisters:
        valid_range = vaem_ranges.get(setting.name)
        if valid_range is None:
            raise ValueError(f"VaemIndex {setting.name} is not a setting")

        if value not in range(*valid_range) and valve_id not in range(1, 9):
            raise ValueError(
                f"{setting.name} must be in range {valid_range[0]} - {valid_range[1] - 1} and valve_id -> 1-8"
            )

        data = create_setting_registers(
            setting,
            valve_id - 1,
            VaemAccess.Write.value,
            int(value),
        )
        return self._transfer_vaem_registers(data)

    def set_valve_settings(
        self, valve_id, settings: ValveSettings | dict[str, int] | None
    ):
        """Configure settings for a specific valve. This method allows setting various
        parameters for a given valve.

        Args:
            valve_id: Valve ID (1-8)
            settings: ValveSettings object, dict of settings, or None for defaults
        """
        if valve_id not in range(1, 9):
            raise ValueError("Valve_id must be between 1-8")

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
            self._set_valve_setting(valve_id, setting, value)

    @clear_and_raise_error
    def save_settings(self) -> VaemRegisters:
        data = VaemRegisters(
            access=VaemAccess.Write.value,
            dataType=VaemDataType.UINT32.value,
            paramIndex=VaemIndex.SaveParameters.value,
            paramSubIndex=0,
            errorRet=0,
            transferValue=99999,
        )

        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def _read_valve_setting(self, valve_id, setting: VaemIndex) -> VaemRegisters:
        """Read settings for a specific valve."""
        # Check if parameter is actually a setting
        if setting.name not in vaem_parameters:
            raise ValueError(f"VaemIndex {setting.name} is not a setting")

        data = create_setting_registers(
            setting,
            valve_id - 1,  # Valve id starts at 0 for settings
            VaemAccess.Read.value,
        )
        return self._transfer_vaem_registers(data)

    def read_valve_settings(self, valve_id: int):
        """Read all settings for a specific valve and returns them as a ValveSettings object"""
        if valve_id not in range(1, 9):
            raise ValueError("Valve_id must be between 1-8")

        settings: dict[str, int] = {}
        for setting in vaem_parameters:
            value = self._read_valve_setting(valve_id, getattr(VaemIndex, setting))
            if value is not None:
                settings.update({setting: value.transferValue})

        return ValveSettings.from_dict(settings)

    ### VALVE OPERATIONS ###
    @clear_and_raise_error
    def open_valves(self) -> VaemRegisters:
        """Start all valves that are selected"""
        self._reset_control_word()
        time.sleep(0.1)
        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.StartValves.value
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def close_valves(self) -> VaemRegisters:
        """Close all valves"""
        self._reset_control_word()
        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.StopValves.value
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def clear_error(self) -> VaemRegisters:
        """If any error occurs in valve opening, must be cleared with this opperation."""
        self._reset_control_word()
        data = create_controlword_registers(
            VaemAccess.Write.value, VaemControlWords.ResetErrors.value
        )
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def _reset_control_word(self) -> VaemRegisters:
        """Reset control word"""
        data = create_controlword_registers(VaemAccess.Write.value, 0)
        return self._transfer_vaem_registers(data)

    @clear_and_raise_error
    def _get_selected_valves(self) -> VaemRegisters:
        data = create_select_valve_registers(VaemAccess.Read.value, 0)
        return self._transfer_vaem_registers(data)

    def read_valves_state(self) -> tuple:
        resp = self._get_selected_valves()

        def convert_to_reverse_binary_list() -> tuple:
            """See documentation pdf on how to open multiple valves."""
            binary_string = format(resp.transferValue, "08b")
            return tuple(int(bit) for bit in reversed(binary_string))

        return convert_to_reverse_binary_list()

    @clear_and_raise_error
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

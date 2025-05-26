from enum import IntEnum, Enum
from dataclasses import dataclass
import struct


valveSettings = {
    "NominalVoltage": 24000,
    "ResponseTime": 500,
    "TimeDelay": 0,
    "PickUpTime": 125,
    "InrushCurrent": 300,
    "HitNHold": 100,
    "HoldingCurrent": 100,
}

vaemValveIndex = {
    1: 0x01,
    2: 0x02,
    3: 0x04,
    4: 0x08,
    5: 0x10,
    6: 0x20,
    7: 0x40,
    8: 0x80,
    "AllValves": 255,
}


@dataclass(frozen=True)
class VaemRegisters:
    access: int
    dataType: int
    paramIndex: int
    paramSubIndex: int
    errorRet: int
    transferValue: int

    @classmethod
    def from_dict(self, data: dict) -> "VaemRegisters":
        """Constructs a VaemRegisters object from a dictionary."""
        if data is None or len(data) == 0:
            return None
        return VaemRegisters(
            access=data["access"],
            dataType=data["dataType"],
            paramIndex=data["paramIndex"],
            paramSubIndex=data["paramSubIndex"],
            errorRet=data["errorRet"],
            transferValue=data["transferValue"],
        )

    def to_dict(self) -> dict:
        """Converts the VaemRegisters object to a dictionary."""
        return self.__dict__

    @classmethod
    def from_list(cls, registers: list[int]) -> "VaemRegisters":
        """Constructs a VaemRegisters object from a list of integers."""
        if registers is None or len(registers) == 0:
            return None
        return _deconstruct_registers(registers)

    def to_list(self) -> list[int]:
        """Converts the VaemRegisters object to a list of integers."""
        return _construct_registers(self)


def _construct_registers(vaem_reg: VaemRegisters) -> list[int]:
    data = vaem_reg.to_dict()
    tmp = struct.pack(
        ">BBHBBQ",
        data["access"],
        data["dataType"],
        data["paramIndex"],
        data["paramSubIndex"],
        data["errorRet"],
        data["transferValue"],
    )

    return [(tmp[i] << 8) + tmp[i + 1] for i in range(0, len(tmp) - 1, 2)]


def _deconstruct_registers(registers: list[int]) -> VaemRegisters:
    if registers is None or len(registers) == 0:
        return None

    access = (registers[0] & 0xFF00) >> 8
    dataType = registers[0] & 0x00FF
    paramIndex = registers[1]
    paramSubIndex = (registers[2] & 0xFF00) >> 8
    errorRet = registers[2] & 0x00FF

    transferValue = sum(registers[len(registers) - 1 - i] << (i * 16) for i in range(4))

    return VaemRegisters(
        access=access,
        dataType=dataType,
        paramIndex=paramIndex,
        paramSubIndex=paramSubIndex,
        errorRet=errorRet,
        transferValue=transferValue,
    )


class VaemAccess(IntEnum):
    Read = 0
    Write = 1


class VaemDataType(IntEnum):
    UINT8 = 1
    UINT16 = 2
    UINT32 = 3
    UINT64 = 4


class VaemIndex(IntEnum):
    ControlWord = 0x01
    StatusWord = 0x02
    NominalVoltage = 0x04
    InrushCurrent = 0x05
    HoldingCurrent = 0x06
    ResponseTime = 0x07
    PickUpTime = 0x08
    OperatingMode = 0x09
    SaveParameters = 0x11
    SelectValve = 0x13
    TimeDelay = 0x16
    HitNHold = 0x2E


"""
class VaemValveIndex(IntEnum):
    Valve1 = 0x01
    Valve2 = 0x02
    Valve3 = 0x04
    Valve4 = 0x08
    Valve5 = 0x10
    Valve6 = 0x20
    Valve7 = 0x40
    Valve8 = 0x80
    AllValves = 255
"""


class VaemRanges(Enum):
    NominalVoltage = (8000, 24000 + 1)
    InrushCurrent = (20, 1000 + 1)
    HoldingCurrent = (20, 400 + 1)
    ResponseTime = (1, (2**32) - 1 + 1)
    PickUpTime = (1, 500 + 1)
    TimeDelay = (0, (2**32) - 1 + 1)
    HitNHold = (0, 1000 + 1)
    SelectValve = (0, 255 + 1)


class VaemControlWords(IntEnum):
    StartValves = 0x01
    StopValves = 0x04
    ResetErrors = 0x08


class VaemOperatingMode(IntEnum):
    OpMode1 = 0x00
    OpMode2 = 0x01
    OpMode3 = 0x02


def parse_statusword(statusWord: int):
    status = {}
    status["Status"] = statusWord & 0x01
    status["Error"] = (statusWord & 0x08) >> 3
    status["Readiness"] = (statusWord & 0x10) >> 4
    status["OperatingMode"] = (statusWord & 0xC0) >> 6
    status["Valve1"] = (statusWord & 0x100) >> 8
    status["Valve2"] = (statusWord & 0x200) >> 9
    status["Valve3"] = (statusWord & 0x400) >> 10
    status["Valve4"] = (statusWord & 0x800) >> 11
    status["Valve5"] = (statusWord & 0x1000) >> 12
    status["Valve6"] = (statusWord & 0x2000) >> 13
    status["Valve7"] = (statusWord & 0x4000) >> 14
    status["Valve8"] = (statusWord & 0x8000) >> 15
    return status


SETTING_DATA_TYPES = {
    VaemIndex.NominalVoltage: VaemDataType.UINT16,
    VaemIndex.ResponseTime: VaemDataType.UINT32,
    VaemIndex.InrushCurrent: VaemDataType.UINT16,
    VaemIndex.HoldingCurrent: VaemDataType.UINT16,
    VaemIndex.PickUpTime: VaemDataType.UINT16,
    VaemIndex.TimeDelay: VaemDataType.UINT32,
    VaemIndex.HitNHold: VaemDataType.UINT32,
    VaemIndex.SelectValve: VaemDataType.UINT8,
}


def create_setting_registers(
    param: VaemIndex, valve: int, operation: int, **settings
) -> VaemRegisters:
    return VaemRegisters(
        access=operation,
        dataType=SETTING_DATA_TYPES[param].value,
        paramIndex=param.value,
        paramSubIndex=valve,
        errorRet=0,
        transferValue=settings.get(param.name, 0),
    )


def create_select_valve_registers(operation: int, valve_code: int) -> VaemRegisters:
    return VaemRegisters(
        access=operation,
        dataType=VaemDataType.UINT8.value,
        paramIndex=VaemIndex.SelectValve.value,
        paramSubIndex=0,
        errorRet=0,
        transferValue=valve_code,
    )


def create_controlword_registers(operation: int, control_word: int) -> VaemRegisters:
    return VaemRegisters(
        access=operation,
        dataType=VaemDataType.UINT16.value,
        paramIndex=VaemIndex.ControlWord.value,
        paramSubIndex=0,
        errorRet=0,
        transferValue=control_word,
    )

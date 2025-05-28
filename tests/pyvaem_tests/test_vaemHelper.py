import pytest
from pyvaem.vaemHelper import VaemIndex, VaemRegisters, ValveSettings


def test_when_registers_created_from_empty_list_raises_error():
    with pytest.raises(ValueError):
        VaemRegisters.from_list([])


@pytest.mark.parametrize(
    "input_list, expected_registers",
    [
        (
            [1, 2, 3, 4, 5, 6],
            VaemRegisters(
                access=0,
                dataType=1,
                paramIndex=2,
                paramSubIndex=0,
                errorRet=3,
                transferValue=0x3000400050006,
            ),
        ),
    ],
)
def test_when_registers_created_from_list_returns_as_expected(
    input_list, expected_registers
):
    registers = VaemRegisters.from_list(input_list)
    assert registers == expected_registers


@pytest.mark.parametrize(
    "registers, expected_list",
    [
        (
            VaemRegisters(
                access=0,
                dataType=1,
                paramIndex=2,
                paramSubIndex=0,
                errorRet=3,
                transferValue=0x3000400050006,
            ),
            [1, 2, 3, 3, 4, 5, 6],
        ),
    ],
)
def test_settings_returned_as_list_returns_are_as_expected(
    registers: "VaemRegisters", expected_list
):
    register_list = registers.to_list()
    assert register_list == expected_list


def test_settings_returned_as_enum_dict_are_as_expected():
    settings = ValveSettings()
    assert settings.to_enum_dict() == {
        VaemIndex.NominalVoltage: 24000,
        VaemIndex.ResponseTime: 500,
        VaemIndex.TimeDelay: 0,
        VaemIndex.PickUpTime: 125,
        VaemIndex.InrushCurrent: 300,
        VaemIndex.HitNHold: 100,
        VaemIndex.HoldingCurrent: 100,
    }

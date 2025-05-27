from pyvaem.vaemHelper import VaemRegisters

def test_when_registers_created_from_empty_list_returns_none():
    registers = VaemRegisters.from_list([])
    assert registers is None

def test_when_registers_created_from_list_returns_as_expected():
    registers = VaemRegisters.from_list([1, 2, 3, 4, 5, 6])
    assert registers == VaemRegisters(
        access=0,
        dataType=1,
        paramIndex=2,
        paramSubIndex=0,
        errorRet=3,
        transferValue=0x3000400050006
    )




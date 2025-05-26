import logging

from pyvaem.VaemDriver import vaemDriver
from pyvaem.dataTypes import VaemConfig


if __name__ == "__main__":
    vaemConfig = VaemConfig("192.168.8.118", 502, 0)

    try:
        vaem = vaemDriver(vaemConfig, logger=logging)
    except Exception as e:
        print(e)

    def func():
        vaem._vaem_init()
        print(vaem.get_status())
        vaem.select_valve(3)
        print(vaem.get_status())
        vaem.deselect_valve(3)
        print(vaem.get_status())
        vaem.select_valve(7)
        print(vaem.get_status())
        vaem.deselect_valve(7)
        print(vaem.get_status())

    func()

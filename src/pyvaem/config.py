from dataclasses import dataclass

from pyvaem.utils import VaemIndex


@dataclass
class VaemConfig:
    ip: str
    port: int
    slave_id: int


@dataclass(frozen=True)
class ValveSettings:
    NominalVoltage: int = 24000
    ResponseTime: int = 500
    TimeDelay: int = 0
    PickUpTime: int = 125
    InrushCurrent: int = 300
    HitNHold: int = 100
    HoldingCurrent: int = 100

    # Mapping from field names to VaemIndex enums
    _FIELD_TO_ENUM = {
        "NominalVoltage": VaemIndex.NominalVoltage,
        "ResponseTime": VaemIndex.ResponseTime,
        "TimeDelay": VaemIndex.TimeDelay,
        "PickUpTime": VaemIndex.PickUpTime,
        "InrushCurrent": VaemIndex.InrushCurrent,
        "HitNHold": VaemIndex.HitNHold,
        "HoldingCurrent": VaemIndex.HoldingCurrent,
    }

    @classmethod
    def from_dict(cls, data: dict | None = None) -> "ValveSettings":
        """Create ValveSettings from dictionary with defaults for missing values."""
        if not data:
            return cls()
        return cls(**data)

    def to_dict(self) -> dict:
        return self.__dict__

    def to_enum_dict(self) -> dict[VaemIndex, int]:
        """Convert to dict with VaemIndex keys."""
        return {
            self._FIELD_TO_ENUM[field_name]: value
            for field_name, value in self.__dict__.items()
            if field_name in self._FIELD_TO_ENUM
        }

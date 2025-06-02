# 🐍 PyVaem

## 📋 Overview

This Python API provides control for the [Festo VAEM](https://www.festo.com/de/en/a/8088772/) valve control module via Modbus TCP/IP communication. It is based on the [original VAEM driver](https://github.com/Festo-se/VAEM) and features comprehensive refactoring and improvements.

## 🛠️ Requirements

- **Python**: 3.10 or higher

### 📚 Core Dependencies

- [PyModbus v3.0+](https://pymodbus.readthedocs.io/)

## 🚀 Installation

### Option 1: From PyPI (Recommended)

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the latest release from PyPI
pip install pyvaem
```

### Option 2: From GitHub Releases

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the latest release from GitHub
pip install https://github.com/jlmoraleshellin/pyvaem/releases/download/v1.0.0/pyvaem-1.0.0-py3-none-any.whl
```

## 📖 Quick Start

### Basic Usage

```python
from pyvaem import VaemDriver, VaemConfig, ValveSettings

# Set the VAEM connection configuration
config = VaemConfig(
    ip='192.168.1.100',
    port=502, # Default VAEM port
    slave_id=1
)

# Initialize the driver
vaem = VaemDriver(config)

# Select and open a single valve
vaem.select_valve(1)  # Select valve 1
vaem.open_valves()    # Open selected valves

# Close all valves before 
vaem.close_valves()

# Select multiple valves at once
valve_states = [1, 0, 1, 0, 0, 0, 0, 0]  # Open valves 1 and 3
vaem.select_valves(valve_states)
vaem.open_valves()

vaem.close_valves()
```

### Valve Configuration

```python
# Configure valve settings
settings = ValveSettings(
    NominalVoltage=24000,
    InrushCurrent=300,
    HoldingCurrent=100,
    ResponseTime=500,
    PickUpTime=125,
    TimeDelay=0,
    HitNHold=100
)

# You can also specify only the settings to change - others use defaults
settings = ValveSettings(
    InrushCurrent=300,
    HoldingCurrent=100,
    ResponseTime=500,
    PickUpTime=125,
    # NominalVoltage will be 24000 (default)
    # TimeDelay will be 0 (default)
    # HitNHold will be 100 (default)
)

# Apply settings to valve 1
vaem.set_valve_settings(1, settings)

# Or use a dictionary for better compatibility
settings_dict = {
    'NominalVoltage': 12000,
    'InrushCurrent': 250
    # All other parameter will use default values
}
vaem.set_valve_settings(2, settings_dict)

# Save settings to device memory (optional)
vaem.save_settings()
```

## 📝 Complete usage example

See [`example_usage.py`](src/example_usage.py).

## 🎯 API Reference

### Core classes and methods

#### VaemDriver

The main driver class for controlling VAEM devices.

**Constructor:**

- `VaemDriver(vaem_config: VaemConfig)`

#### VaemConfig

Configuration dataclass for VAEM connection parameters.

```python
@dataclass
class VaemConfig:
    ip: str          # Device IP address
    port: int        # Modbus TCP port (typically 502)
    slave_id: int    # Modbus slave ID
```

#### ValveSettings

Configuration dataclass for valve parameters with VAEM defaults.

```python
@dataclass
class ValveSettings:
    NominalVoltage: int = 24000    # Voltage (8000-24000 mV)
    ResponseTime: int = 500        # Response time (1-2³²-1 ms)
    TimeDelay: int = 0             # Time delay (0-2³²-1 ms)
    PickUpTime: int = 125          # Pick-up time (1-500 ms)
    InrushCurrent: int = 300       # Inrush current (20-1000 mA)
    HitNHold: int = 100            # Hit & hold (0-1000 ms)
    HoldingCurrent: int = 100      # Holding current (20-400 mA)
```

#### Valve Selection Methods

- `select_valve(valve_id: int)` - Select a single valve (1-8)
- `deselect_valve(valve_id: int)` - Deselect a single valve (1-8)
- `select_valves(states: list[int])` - Select multiple valves with 8-element list of 0s and 1s
- `select_all_valves()` - Select all valves
- `deselect_all_valves()` - Deselect all valves
- `read_valves_state()` - Get current valve selection as tuple

#### Valve Operation Methods

- `open_valves()` - Open all selected valves
- `close_valves()` - Close all valves
- `clear_error()` - Clear any device errors

#### Configuration Methods

- `set_valve_settings(valve_id: int, settings: ValveSettings | dict | None)` - Configure valve parameters
- `read_valve_settings(valve_id: int)` - Read current valve settings
- `save_settings()` - Save current configuration to device memory

#### Status Methods

- `get_status()` - Get device status including valve states and errors

## 🚨 Error Handling

The driver includes comprehensive error handling with specific exception types:

- `IndexError` - Invalid parameter index or subindex
- `PermissionError` - Read/write operation not allowed
- `ValueError` - Parameter value out of range or invalid
- `TypeError` - Incorrect data type
- `RuntimeError` - Command execution failed
- `ConnectionError` - Failed to connect to VAEM device

All valve operations are automatically wrapped with error checking and clearing.

## 📚 Documentation

For detailed documentation check the [operating manual](docs/VAEM-V-S8EPRS2_operating-instr_2021-10a_8144872g1.pdf)

## 🤝 Contributing

Contributions are welcome!

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Attribution

This project is based on the original VAEM driver developed by Milen Kolev (<milen.kolev@festo.com>) and the Festo team. The original project provided the foundation for this improved implementation.

**Original Repository**: [Festo VAEM Driver](https://github.com/Festo-se/VAEM)

## 📧 Contact

For questions, issues, or contributions:

- **Email**: <jlmoraleshellin@gmail.com>

## 🔄 Changelog

### Version 1.0.0 (Current)

- Complete rewrite with improved architecture
- Enhanced error handling with specific exception types
- Comprehensive valve configuration with ValveSettings dataclass
- Improved logging and connection management
- Better API design with clear method separation
- Support for multiple valve selection patterns
- Automatic error clearing on operations

### Version 0.0.2 (Original)

- Basic VAEM control functionality
- Modbus TCP communication
- Simple valve operations

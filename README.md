# 🐍 PyVaem

## 📋 Overview

This is an improved and maintained Python driver for Festo VAEM (Valve control module) devices. This project is based on the original VAEM driver but has been significantly refactored, tested, and enhanced for better reliability and usability.

## 🛠️ Requirements

- **Python**: 3.8 or higher

### 📚 Core Dependencies
- [PyModbus v3.0+](https://pymodbus.readthedocs.io/)

## 🚀 Installation

### Option 1: From Source
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

## 📖 Quick Start

### Basic Usage
In progress...

## 🎯 API Reference

### Core Methods
- `configure_valves(valve_config: dict)` - Set valve parameters
- `save_settings()` - Save current configuration to device
- `select_valves(valve_list: list)` - Select valves to open
- `select_valves(valve_list: list)` - Select valves to open
- `open_valve()` - Open selected valve
- `close_valve()` - Close all valves
- `clear_error()` - Clear any device errors

### Configuration Options
```python
config = VaemConfig(
    ip='192.168.1.100',        # Device IP address
    port=502,                  # Modbus TCP port
    slave_id=1,                # Modbus slave ID
)
```

## 📝 Examples

See `exampleVaem.py` for a usage example.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Attribution

This project is based on the original VAEM driver developed by Milen Kolev (milen.kolev@festo.com) and the Festo team. The original project provided the foundation for this improved implementation.

**Original Repository**: [Link to original if still available](https://github.com/Festo-se/VAEM)

## 📧 Contact

For questions, issues, or contributions:
- **Email**: [jlmoraleshellin@gmail.com]

## 🔄 Changelog

### Version 1.0.0 (Current)
- Reqrite with improved architecture
- Improved error handling and logging
- More...

### Version 0.0.2 (Original)
- Basic VAEM control functionality
- Modbus TCP communication
- Simple valve operations
# DASS - Data Acquisition System for Serial/ModBus

This repository contains a modular, well-structured implementation of a Data Acquisition System (DASS) for serial and Modbus communication interfaces.

## Overview

DASS is a Python-based GUI application designed for real-time data acquisition, monitoring, and logging. The implementation follows best practices with modular architecture, comprehensive documentation, and PEP 8 compliance.

## Features

- **Modular Architecture**: Separate classes for serial communication, Modbus protocol, data logging, plotting, and UI management
- **Serial Port Communication**: Full support for serial port connections with configurable baud rates
- **Modbus Support**: ModBus RTU protocol support for industrial devices
- **Real-time Plotting**: Live visualization of up to 3 data channels with automatic scaling
- **Automatic Data Logging**: CSV-based logging with timestamps and configurable channel names
- **User-friendly GUI**: Intuitive Tkinter-based interface with activity logging

## Architecture

The application is organized into the following classes:

- `SerialHandler`: Manages serial port connections and data transfer
- `ModbusHandler`: Handles ModBus protocol communication
- `DataLogger`: Manages CSV file logging with timestamps
- `PlotManager`: Real-time plotting with matplotlib integration
- `UIManager`: Centralized UI component creation and management
- `DASSApplication`: Main application controller coordinating all components

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- pyserial >= 3.5
- pymodbus >= 3.0.0
- matplotlib >= 3.5.0

## Download

### Option 1: Clone with Git (Recommended)

If you have Git installed:

```bash
git clone https://github.com/faturahman634/das.git
cd das
```

### Option 2: Download ZIP File

If you don't have Git:

1. Go to https://github.com/faturahman634/das
2. Click the green **"Code"** button
3. Select **"Download ZIP"**
4. Extract the ZIP file to your desired location
5. Open a terminal/command prompt in the extracted folder

### Option 3: Download Single File

For quick testing, download just the main file:

1. Go to https://github.com/faturahman634/das/blob/main/DASS_Ver_1_channel_name_3_auto_save.py
2. Click the **"Raw"** button
3. Right-click and **"Save As"** to save the file
4. Install dependencies manually (see below)

## Installation

After downloading, install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install pyserial pymodbus matplotlib
```

## Usage

Run the application:
```bash
python DASS_Ver_1_channel_name_3_auto_save.py
```

### Using the Application

1. **Connect to Device**:
   - Select connection type (Serial or ModBus)
   - Choose the appropriate COM port
   - Set the baudrate (default: 9600)
   - Click "Connect"

2. **Configure Channels**:
   - Enter custom names for each channel (up to 3 channels)
   - Names will be used in logs and plots

3. **Start Acquisition**:
   - Click "Start Acquisition" to begin data collection
   - Data is automatically logged to CSV files in the `logs/` directory
   - Real-time plot updates as data is acquired

4. **Stop Acquisition**:
   - Click "Stop Acquisition" to end data collection
   - Log files are automatically saved

## Code Quality

- **PEP 8 Compliant**: Code follows Python style guidelines
- **Type Hints**: Functions include type annotations for better code clarity
- **Comprehensive Documentation**: All classes and methods include docstrings
- **Error Handling**: Proper exception handling with user-friendly error messages

## Project Structure

```
das/
├── DASS_Ver_1_channel_name_3_auto_save.py  # Main application
├── requirements.txt                         # Python dependencies
├── README.md                                # This file
└── logs/                                    # Auto-generated log directory
```

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 guidelines
- All functions include docstrings
- Changes maintain backward compatibility

## License

This project is open source and available for educational and commercial use.
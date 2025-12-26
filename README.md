# DASS - Data Acquisition System for Serial/ModBus

This repository contains a modular, well-structured implementation of a Data Acquisition System (DASS) for serial and Modbus communication interfaces.

## Overview

DASS is a Python-based GUI application designed for real-time data acquisition, monitoring, and logging. The implementation follows best practices with modular architecture, comprehensive documentation, and PEP 8 compliance.

## Features

### Core Capabilities
- **Modular Architecture**: Separate classes for serial communication, Modbus protocol, data logging, plotting, and UI management
- **Serial Port Communication**: Full support for serial port connections with configurable baud rates
- **Real-time Plotting**: Live visualization of multiple data channels with automatic scaling
- **Automatic Data Logging**: CSV-based logging with timestamps and configurable channel names
- **User-friendly GUI**: Intuitive Tkinter-based interface with activity logging

### Advanced ModBus Support
- **Multiple Slave IDs**: Support for up to 4 ModBus slave devices
- **Multiple Addresses**: Up to 20 register addresses per slave ID
- **Flexible Data Types**: INT16, UINT16, INT32, UINT32, FLOAT32
- **16/32-bit Support**: Configurable register width for each address
- **Easy Configuration**: GUI dialog for setting up ModBus parameters

### Data Visualization & Export
- **8 Channel Support**: Monitor up to 8 data channels simultaneously
- **Signal Conditioning**: Per-channel Zero offset, Multiplier, and Gain adjustment
- **Unified Plot**: Single real-time plot showing all 8 channels with color-coding
- **Numeric Displays**: Real-time numeric value display for each channel in main window
- **Separate Numeric Window**: Dedicated window with large numeric displays
- **Plot Printing**: Direct print functionality for plots
- **Plot Export**: Save plots as PNG, PDF, or SVG (300 DPI)
- **Manual Plot Setup**: Configure plot title, labels, and grid
- **Custom CSV Naming**: Optional custom filenames for log files

### Signal Conditioning
Each of the 8 channels has configurable signal conditioning parameters:
- **Zero Offset**: Baseline adjustment (add/subtract from raw value)
- **Multiplier**: Scale factor for the signal
- **Gain**: Amplification factor

Formula applied: `Display Value = (Raw Value + Zero) × Multiplier × Gain`

## Architecture

The application is organized into the following classes:

- `SerialHandler`: Manages serial port connections and data transfer
- `ModbusHandler`: Handles ModBus protocol communication with data type conversion
- `DataLogger`: Manages CSV file logging with timestamps and custom filenames
- `PlotManager`: Real-time unified plotting with matplotlib integration for all 8 channels
- `NumericDisplayWindow`: Separate window for large numeric value displays
- `UIManager`: Centralized UI component creation and management
- `DASSApplication`: Main application controller coordinating all components with signal conditioning

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

#### Basic Setup

1. **Connect to Device**:
   - Select connection type (Serial or ModBus)
   - Choose the appropriate COM port
   - Set the baudrate (default: 9600)
   - Click "Connect"

2. **Configure Channels**:
   - Enter custom names for each channel
   - View real-time numeric values during acquisition
   - Names will be used in logs and plots

3. **Start Acquisition**:
   - (Optional) Enter a custom CSV filename
   - Click "Start Acquisition" to begin data collection
   - Data is automatically logged to CSV files in the `logs/` directory
   - Real-time plot and numeric displays update as data is acquired

4. **Stop Acquisition**:
   - Click "Stop Acquisition" to end data collection
   - Log files are automatically saved

#### Advanced ModBus Configuration

1. **Open ModBus Configuration**:
   - Click "Configure ModBus Addresses" button
   - A dialog with tabs for 4 slave IDs will open

2. **Configure Addresses**:
   - Select a Slave ID tab (1-4)
   - For each address you want to monitor:
     - Enter the register address
     - Select data type (INT16, UINT16, INT32, UINT32, FLOAT32)
     - Enter a channel name
     - Check the "Enable" box

3. **Save Configuration**:
   - Click "Save Configuration"
   - Status shows number of configured addresses
   - Configured addresses will be read during acquisition

#### Plot Management

- **Print Plot**: Click "Print Plot" to send the current plot to your default printer
- **Save Plot**: Click "Save Plot" and choose format (PNG, PDF, or SVG)
- **Configure Plot**: Click "Configure Plot" to customize:
  - Plot title
  - X-axis label
  - Y-axis label
  - Grid on/off

#### Custom CSV Filenames

- Enter a custom filename in the "CSV Filename" field (optional)
- Leave empty for automatic timestamp-based naming
- Extension `.csv` is added automatically

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
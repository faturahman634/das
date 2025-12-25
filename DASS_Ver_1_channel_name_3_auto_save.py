"""
DASS - Data Acquisition System for Serial/ModBus
A modular, maintainable implementation for serial and ModBus data acquisition
with real-time plotting and data logging capabilities.

This module provides a complete GUI application for:
- Serial port communication
- ModBus protocol support
- Real-time data plotting
- Automatic data logging
- Multi-channel monitoring
"""

import sys

# Check for required dependencies
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
except ImportError:
    print("ERROR: tkinter is not installed.")
    print("Please install tkinter (usually included with Python).")
    sys.exit(1)

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial is not installed.")
    print("Please install it with: pip install pyserial")
    sys.exit(1)

try:
    from pymodbus.client import ModbusSerialClient
except ImportError:
    print("ERROR: pymodbus is not installed.")
    print("Please install it with: pip install pymodbus")
    sys.exit(1)

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:
    print("ERROR: matplotlib is not installed.")
    print("Please install it with: pip install matplotlib")
    sys.exit(1)

import threading
import time
import csv
import os
import random
from datetime import datetime
from typing import List, Optional, Dict, Any


# Constants
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT = 1
DEFAULT_MODBUS_SLAVE_ID = 1
DEFAULT_CHANNEL_COUNT = 8  # Expanded to 8 channels
MAX_SLAVE_IDS = 4
MAX_ADDRESSES_PER_ID = 20
MAX_DATA_POINTS = 100

# Signal conditioning defaults
DEFAULT_ZERO = 0.0
DEFAULT_MULTIPLIER = 1.0
DEFAULT_GAIN = 1.0
LOG_DIRECTORY = "logs"

# ModBus data type options
MODBUS_DATA_TYPES = {
    'INT16': {'bits': 16, 'registers': 1, 'signed': True},
    'UINT16': {'bits': 16, 'registers': 1, 'signed': False},
    'INT32': {'bits': 32, 'registers': 2, 'signed': True},
    'UINT32': {'bits': 32, 'registers': 2, 'signed': False},
    'FLOAT32': {'bits': 32, 'registers': 2, 'signed': None},
}


class SerialHandler:
    """
    Handles serial port communication.
    Provides methods for port selection, connection, and data transmission.
    """

    def __init__(self):
        """Initialize the serial handler."""
        self.connection: Optional[serial.Serial] = None
        self.is_connected = False

    def get_available_ports(self) -> List[str]:
        """
        Get list of available serial ports.

        Returns:
            List of available port names
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE,
                timeout: float = DEFAULT_TIMEOUT) -> bool:
        """
        Connect to a serial port.

        Args:
            port: Serial port name
            baudrate: Communication speed
            timeout: Read timeout in seconds

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            self.is_connected = True
            return True
        except serial.SerialException as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to {port}: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from the serial port."""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False

    def write(self, data: bytes) -> bool:
        """
        Write data to the serial port.

        Args:
            data: Bytes to write

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected or not self.connection:
            return False
        try:
            self.connection.write(data)
            return True
        except serial.SerialException:
            return False

    def read(self, size: int = 1) -> bytes:
        """
        Read data from the serial port.

        Args:
            size: Number of bytes to read

        Returns:
            Read bytes
        """
        if not self.is_connected or not self.connection:
            return b''
        try:
            return self.connection.read(size)
        except serial.SerialException:
            return b''


class ModbusHandler:
    """
    Handles ModBus protocol communication.
    Supports reading holding registers and coils.
    """

    def __init__(self):
        """Initialize the ModBus handler."""
        self.client: Optional[ModbusSerialClient] = None
        self.is_connected = False

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE,
                timeout: float = DEFAULT_TIMEOUT) -> bool:
        """
        Connect to a ModBus device.

        Args:
            port: Serial port name
            baudrate: Communication speed
            timeout: Response timeout in seconds

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            self.is_connected = self.client.connect()
            return self.is_connected
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect ModBus on {port}: {str(e)}")

    def disconnect(self) -> None:
        """Disconnect from the ModBus device."""
        if self.client and self.is_connected:
            self.client.close()
            self.is_connected = False

    def read_holding_registers(self, address: int, count: int = 1,
                               slave_id: int = DEFAULT_MODBUS_SLAVE_ID) -> Optional[List[int]]:
        """
        Read holding registers from ModBus device.

        Args:
            address: Starting register address
            count: Number of registers to read
            slave_id: ModBus slave ID

        Returns:
            List of register values or None on error
        """
        if not self.is_connected or not self.client:
            return None
        try:
            result = self.client.read_holding_registers(
                address=address,
                count=count,
                slave=slave_id
            )
            if not result.isError():
                return result.registers
            return None
        except Exception:
            return None

    def read_coils(self, address: int, count: int = 1,
                   slave_id: int = DEFAULT_MODBUS_SLAVE_ID) -> Optional[List[bool]]:
        """
        Read coils from ModBus device.

        Args:
            address: Starting coil address
            count: Number of coils to read
            slave_id: ModBus slave ID

        Returns:
            List of coil values or None on error
        """
        if not self.is_connected or not self.client:
            return None
        try:
            result = self.client.read_coils(
                address=address,
                count=count,
                slave=slave_id
            )
            if not result.isError():
                return result.bits[:count]
            return None
        except Exception:
            return None

    def read_register_as_type(self, address: int, data_type: str,
                              slave_id: int = DEFAULT_MODBUS_SLAVE_ID) -> Optional[float]:
        """
        Read register(s) and convert to specified data type.

        Args:
            address: Starting register address
            data_type: Data type (INT16, UINT16, INT32, UINT32, FLOAT32)
            slave_id: ModBus slave ID

        Returns:
            Converted value or None on error
        """
        if data_type not in MODBUS_DATA_TYPES:
            return None

        type_info = MODBUS_DATA_TYPES[data_type]
        registers = self.read_holding_registers(
            address, type_info['registers'], slave_id
        )

        if not registers:
            return None

        try:
            if data_type == 'INT16':
                value = registers[0]
                return value if value < 32768 else value - 65536
            elif data_type == 'UINT16':
                return float(registers[0])
            elif data_type == 'INT32':
                value = (registers[0] << 16) | registers[1]
                return value if value < 2147483648 else value - 4294967296
            elif data_type == 'UINT32':
                return float((registers[0] << 16) | registers[1])
            elif data_type == 'FLOAT32':
                import struct
                bytes_data = struct.pack('>HH', registers[0], registers[1])
                return struct.unpack('>f', bytes_data)[0]
            return None
        except Exception:
            return None

    def read_multiple_addresses(self, slave_configs: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Read multiple addresses from multiple slave IDs.

        Args:
            slave_configs: List of dicts with 'slave_id', 'address', 'data_type', 'name'

        Returns:
            Dictionary mapping names to values
        """
        results = {}
        for config in slave_configs:
            value = self.read_register_as_type(
                config['address'],
                config['data_type'],
                config['slave_id']
            )
            if value is not None:
                results[config['name']] = value
        return results


class DataLogger:
    """
    Handles data logging to CSV files.
    Automatically creates log files with timestamps.
    """

    def __init__(self, log_dir: str = LOG_DIRECTORY):
        """
        Initialize the data logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = log_dir
        self.log_file: Optional[str] = None
        self.file_handle: Optional[Any] = None
        self.csv_writer: Optional[Any] = None
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def start_logging(self, channel_names: List[str], custom_filename: str = None) -> None:
        """
        Start logging with specified channel names.

        Args:
            channel_names: List of channel names for CSV header
            custom_filename: Optional custom filename (without path or extension)
        """
        if custom_filename:
            # Use custom filename, add timestamp if needed
            if not custom_filename.endswith('.csv'):
                custom_filename += '.csv'
            self.log_file = os.path.join(self.log_dir, custom_filename)
        else:
            # Default timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = os.path.join(self.log_dir, f"dass_log_{timestamp}.csv")

        self.file_handle = open(self.log_file, 'w', newline='')
        self.csv_writer = csv.writer(self.file_handle)

        # Write header
        header = ['Timestamp'] + channel_names
        self.csv_writer.writerow(header)
        self.file_handle.flush()

    def log_data(self, data: List[Any]) -> None:
        """
        Log a data row.

        Args:
            data: List of data values to log
        """
        if not self.csv_writer or not self.file_handle:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        row = [timestamp] + data
        self.csv_writer.writerow(row)
        self.file_handle.flush()

    def stop_logging(self) -> None:
        """Stop logging and close the file."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.csv_writer = None


class NumericDisplayWindow:
    """
    Separate window showing numeric values for all channels.
    """

    def __init__(self, channel_count: int):
        """
        Initialize numeric display window.

        Args:
            channel_count: Number of channels to display
        """
        self.channel_count = channel_count
        self.window: Optional[tk.Toplevel] = None
        self.value_labels: List[tk.Label] = []
        self.name_labels: List[tk.Label] = []
        self.is_visible = False

    def show(self, parent: tk.Tk, channel_names: List[str]) -> None:
        """
        Show the numeric display window.

        Args:
            parent: Parent window
            channel_names: List of channel names
        """
        if self.window and self.is_visible:
            self.window.lift()
            return

        self.window = tk.Toplevel(parent)
        self.window.title("Numeric Display - All Channels")
        self.window.geometry("500x400")

        # Create header
        header_frame = tk.Frame(self.window, bg='#2c3e50', pady=10)
        header_frame.pack(fill=tk.X)
        tk.Label(
            header_frame, text="Real-Time Channel Values",
            font=('Arial', 14, 'bold'), bg='#2c3e50', fg='white'
        ).pack()

        # Create scrollable frame
        canvas = tk.Canvas(self.window)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create grid for channels
        self.value_labels = []
        self.name_labels = []

        for i in range(self.channel_count):
            # Channel frame
            ch_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, borderwidth=2, pady=10, padx=10)
            ch_frame.grid(row=i, column=0, sticky='ew', padx=10, pady=5)
            scrollable_frame.columnconfigure(0, weight=1)

            # Channel name
            name_label = tk.Label(
                ch_frame,
                text=channel_names[i] if i < len(channel_names) else f"Channel {i+1}",
                font=('Arial', 11, 'bold'),
                anchor='w'
            )
            name_label.pack(side=tk.LEFT, padx=10)
            self.name_labels.append(name_label)

            # Channel value
            value_label = tk.Label(
                ch_frame,
                text="--",
                font=('Arial', 16, 'bold'),
                fg='#2ecc71',
                width=15,
                anchor='e'
            )
            value_label.pack(side=tk.RIGHT, padx=10)
            self.value_labels.append(value_label)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.is_visible = True
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

    def hide(self) -> None:
        """Hide the numeric display window."""
        if self.window:
            self.window.withdraw()
            self.is_visible = False

    def update_value(self, channel_index: int, value: float) -> None:
        """
        Update a channel's numeric display.

        Args:
            channel_index: Index of the channel
            value: New value
        """
        if 0 <= channel_index < len(self.value_labels) and self.is_visible:
            self.value_labels[channel_index].config(text=f"{value:.2f}")

    def update_channel_name(self, channel_index: int, name: str) -> None:
        """
        Update a channel's name.

        Args:
            channel_index: Index of the channel
            name: New name
        """
        if 0 <= channel_index < len(self.name_labels):
            self.name_labels[channel_index].config(text=name)

    def close(self) -> None:
        """Close the numeric display window."""
        if self.window:
            self.window.destroy()
            self.window = None
            self.is_visible = False


class PlotManager:
    """
    Manages real-time plotting of data channels.
    Handles multiple channels with automatic color assignment.
    """

    def __init__(self, parent_frame: tk.Frame, channel_count: int, channel_names: List[str] = None):
        """
        Initialize the plot manager.

        Args:
            parent_frame: Tkinter frame to embed the plot
            channel_count: Number of data channels to plot
            channel_names: Optional list of channel names for legend
        """
        self.channel_count = channel_count
        self.data_buffers: List[List[float]] = [[] for _ in range(channel_count)]
        
        if channel_names is None:
            channel_names = [f'Channel {i+1}' for i in range(channel_count)]

        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.lines: List[Any] = []

        # Initialize plot lines with channel names
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k', 'orange']
        for i in range(channel_count):
            color = colors[i % len(colors)]
            line, = self.ax.plot([], [], f'{color}-', label=channel_names[i], linewidth=1.5)
            self.lines.append(line)

        self.ax.set_xlabel('Sample')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Real-time Data Acquisition - All Channels')
        self.ax.legend(loc='upper left', fontsize=8)
        self.ax.grid(True, alpha=0.3)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent_frame)

    def update_data(self, values: List[float]) -> None:
        """
        Update data for all channels.

        Args:
            values: List of values for all channels
        """
        for i, value in enumerate(values):
            if i < self.channel_count:
                buffer = self.data_buffers[i]
                buffer.append(value)

                # Keep only recent data points
                if len(buffer) > MAX_DATA_POINTS:
                    buffer.pop(0)
        
        # Auto-refresh after update
        self.refresh_plot()

    def refresh_plot(self) -> None:
        """Refresh the plot with current data."""
        for i, (line, buffer) in enumerate(zip(self.lines, self.data_buffers)):
            if buffer:
                x_data = list(range(len(buffer)))
                line.set_data(x_data, buffer)

        # Auto-scale axes
        self.ax.relim()
        self.ax.autoscale_view()

        try:
            self.canvas.draw()
        except Exception:
            pass  # Ignore drawing errors during window close

    def print_plot(self) -> None:
        """Print the current plot."""
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            import tempfile
            import subprocess
            import platform

            # Save to temporary PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name

            with PdfPages(tmp_path) as pdf:
                pdf.savefig(self.figure)

            # Open with default PDF viewer (which has print option)
            if platform.system() == 'Windows':
                os.startfile(tmp_path, 'print')
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '-a', 'Preview', tmp_path])
            else:  # Linux
                subprocess.run(['xdg-open', tmp_path])
        except Exception as e:
            print(f"Error printing plot: {e}")

    def save_plot_image(self, filename: str) -> None:
        """
        Save plot as image file.

        Args:
            filename: Path to save the image
        """
        try:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')
        except Exception as e:
            print(f"Error saving plot: {e}")

    def configure_plot(self, title: str = None, xlabel: str = None,
                       ylabel: str = None, grid: bool = True) -> None:
        """
        Manually configure plot appearance.

        Args:
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Show grid
        """
        if title:
            self.ax.set_title(title)
        if xlabel:
            self.ax.set_xlabel(xlabel)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        self.ax.grid(grid)
        try:
            self.canvas.draw()
        except Exception:
            pass


class UIManager:
    """
    Manages the user interface components.
    Provides methods for creating and updating UI elements.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the UI manager.

        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.widgets: Dict[str, Any] = {}

    def create_labeled_combobox(self, parent: tk.Frame, label: str,
                                values: List[str], row: int,
                                column: int = 0) -> ttk.Combobox:
        """
        Create a labeled combobox widget.

        Args:
            parent: Parent frame
            label: Label text
            values: Combobox values
            row: Grid row
            column: Grid column

        Returns:
            Created combobox widget
        """
        tk.Label(parent, text=label).grid(row=row, column=column, sticky='w', padx=5, pady=2)
        combobox = ttk.Combobox(parent, values=values, state='readonly', width=15)
        combobox.grid(row=row, column=column+1, sticky='ew', padx=5, pady=2)
        if values:
            combobox.current(0)
        return combobox

    def create_labeled_entry(self, parent: tk.Frame, label: str, row: int,
                             column: int = 0, default: str = '') -> tk.Entry:
        """
        Create a labeled entry widget.

        Args:
            parent: Parent frame
            label: Label text
            row: Grid row
            column: Grid column
            default: Default value

        Returns:
            Created entry widget
        """
        tk.Label(parent, text=label).grid(row=row, column=column, sticky='w', padx=5, pady=2)
        entry = tk.Entry(parent, width=18)
        entry.grid(row=row, column=column+1, sticky='ew', padx=5, pady=2)
        if default:
            entry.insert(0, default)
        return entry

    def create_button(self, parent: tk.Frame, text: str, command: Any,
                      row: int, column: int = 0, columnspan: int = 1) -> tk.Button:
        """
        Create a button widget.

        Args:
            parent: Parent frame
            text: Button text
            command: Button command
            row: Grid row
            column: Grid column
            columnspan: Number of columns to span

        Returns:
            Created button widget
        """
        button = tk.Button(parent, text=text, command=command, width=15)
        button.grid(row=row, column=column, columnspan=columnspan, padx=5, pady=5)
        return button

    def create_status_label(self, parent: tk.Frame, text: str = 'Disconnected',
                            row: int = 0, column: int = 0) -> tk.Label:
        """
        Create a status label.

        Args:
            parent: Parent frame
            text: Initial text
            row: Grid row
            column: Grid column

        Returns:
            Created label widget
        """
        label = tk.Label(parent, text=text, fg='red', font=('Arial', 10, 'bold'))
        label.grid(row=row, column=column, columnspan=2, pady=5)
        return label

    def update_status(self, label: tk.Label, text: str, color: str) -> None:
        """
        Update status label.

        Args:
            label: Label widget to update
            text: New text
            color: Text color
        """
        label.config(text=text, fg=color)

    def show_error(self, title: str, message: str) -> None:
        """
        Show error message dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """
        Show information message dialog.

        Args:
            title: Dialog title
            message: Information message
        """
        messagebox.showinfo(title, message)


class DASSApplication:
    """
    Main application class for DASS.
    Coordinates all components and manages the application lifecycle.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the DASS application.

        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title("DASS - Data Acquisition System (Serial/ModBus)")
        self.root.geometry("1000x700")

        # Initialize handlers
        self.serial_handler = SerialHandler()
        self.modbus_handler = ModbusHandler()
        self.data_logger = DataLogger()
        self.ui_manager = UIManager(root)

        # State variables
        self.acquisition_active = False
        self.acquisition_thread: Optional[threading.Thread] = None
        self.channel_count = DEFAULT_CHANNEL_COUNT
        self.channel_entries: List[tk.Entry] = []
        self.channel_value_labels: List[tk.Label] = []  # For numeric display in main window
        self.csv_filename_var = tk.StringVar()  # For custom CSV filename
        self.modbus_configs: List[Dict[str, Any]] = []  # ModBus configurations

        # Signal conditioning parameters (zero, multiplier, gain)
        self.channel_zero: List[tk.StringVar] = []
        self.channel_multiplier: List[tk.StringVar] = []
        self.channel_gain: List[tk.StringVar] = []
        
        # Initialize signal conditioning vars
        for i in range(self.channel_count):
            self.channel_zero.append(tk.StringVar(value=str(DEFAULT_ZERO)))
            self.channel_multiplier.append(tk.StringVar(value=str(DEFAULT_MULTIPLIER)))
            self.channel_gain.append(tk.StringVar(value=str(DEFAULT_GAIN)))
        
        # Plot manager (will be initialized in UI creation)
        self.plot_manager: Optional[PlotManager] = None
        
        # Numeric display window
        self.numeric_display_window: Optional[NumericDisplayWindow] = None
        self.numeric_display_window = NumericDisplayWindow(self.channel_count)

        # Build UI
        self._create_ui()

        # Setup cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_ui(self) -> None:
        """Create the user interface."""
        # Main container
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create sections
        self._create_connection_section(main_frame)
        self._create_modbus_config_section(main_frame)
        self._create_channel_section(main_frame)
        self._create_control_section(main_frame)
        self._create_plot_section(main_frame)
        self._create_log_section(main_frame)

    def _create_connection_section(self, parent: tk.Frame) -> None:
        """Create connection settings section."""
        frame = tk.LabelFrame(parent, text="Connection Settings", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # Get available ports
        available_ports = self.serial_handler.get_available_ports()
        if not available_ports:
            available_ports = ['No ports found']

        # Connection type
        self.conn_type = self.ui_manager.create_labeled_combobox(
            frame, "Connection Type:", ["Serial", "ModBus"], 0
        )

        # Port selection
        self.port_combo = self.ui_manager.create_labeled_combobox(
            frame, "Port:", available_ports, 1
        )

        # Baudrate
        self.baudrate_entry = self.ui_manager.create_labeled_entry(
            frame, "Baudrate:", 2, default=str(DEFAULT_BAUDRATE)
        )

        # Connect button
        self.connect_btn = self.ui_manager.create_button(
            frame, "Connect", self._on_connect, 3, 0, 2
        )

        # Status label
        self.status_label = self.ui_manager.create_status_label(frame, row=4)

    def _create_modbus_config_section(self, parent: tk.Frame) -> None:
        """Create ModBus configuration section."""
        frame = tk.LabelFrame(parent, text="ModBus Configuration (Optional)", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # Add button to open ModBus configuration dialog
        config_btn = tk.Button(
            frame, text="Configure ModBus Addresses",
            command=self._open_modbus_config_dialog,
            width=25
        )
        config_btn.pack(pady=5)

        # Status label showing number of configured addresses
        self.modbus_status_label = tk.Label(
            frame, text="No ModBus addresses configured", fg='gray'
        )
        self.modbus_status_label.pack(pady=2)

    def _open_modbus_config_dialog(self) -> None:
        """Open dialog for configuring ModBus addresses."""
        dialog = tk.Toplevel(self.root)
        dialog.title("ModBus Configuration")
        dialog.geometry("600x500")

        # Instructions
        tk.Label(
            dialog, text="Configure up to 4 Slave IDs with 20 addresses each",
            font=('Arial', 10, 'bold')
        ).pack(pady=10)

        # Create notebook for slave IDs
        from tkinter import ttk
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.temp_modbus_configs = []

        for slave_id in range(1, MAX_SLAVE_IDS + 1):
            # Create tab for each slave ID
            tab = tk.Frame(notebook)
            notebook.add(tab, text=f"Slave ID {slave_id}")

            # Scrollable frame for addresses
            canvas = tk.Canvas(tab)
            scrollbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Header
            tk.Label(scrollable_frame, text="Address", width=10).grid(row=0, column=0, padx=2)
            tk.Label(scrollable_frame, text="Data Type", width=15).grid(row=0, column=1, padx=2)
            tk.Label(scrollable_frame, text="Channel Name", width=20).grid(row=0, column=2, padx=2)
            tk.Label(scrollable_frame, text="Enable", width=8).grid(row=0, column=3, padx=2)

            # Create address configuration rows
            for addr_idx in range(MAX_ADDRESSES_PER_ID):
                row = addr_idx + 1

                addr_entry = tk.Entry(scrollable_frame, width=10)
                addr_entry.grid(row=row, column=0, padx=2, pady=1)
                addr_entry.insert(0, str(addr_idx))

                data_type_var = tk.StringVar(value='UINT16')
                data_type_combo = ttk.Combobox(
                    scrollable_frame, textvariable=data_type_var,
                    values=list(MODBUS_DATA_TYPES.keys()),
                    state='readonly', width=13
                )
                data_type_combo.grid(row=row, column=1, padx=2, pady=1)

                name_entry = tk.Entry(scrollable_frame, width=20)
                name_entry.grid(row=row, column=2, padx=2, pady=1)
                name_entry.insert(0, f"S{slave_id}_A{addr_idx}")

                enable_var = tk.BooleanVar(value=False)
                enable_check = tk.Checkbutton(scrollable_frame, variable=enable_var)
                enable_check.grid(row=row, column=3, padx=2, pady=1)

                # Store references
                self.temp_modbus_configs.append({
                    'slave_id': slave_id,
                    'addr_entry': addr_entry,
                    'data_type_var': data_type_var,
                    'name_entry': name_entry,
                    'enable_var': enable_var
                })

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        # Save button
        save_btn = tk.Button(
            dialog, text="Save Configuration",
            command=lambda: self._save_modbus_config(dialog),
            width=20
        )
        save_btn.pack(pady=10)

    def _save_modbus_config(self, dialog: tk.Toplevel) -> None:
        """Save ModBus configuration from dialog."""
        self.modbus_configs = []

        for config_ui in self.temp_modbus_configs:
            if config_ui['enable_var'].get():
                try:
                    address = int(config_ui['addr_entry'].get())
                    self.modbus_configs.append({
                        'slave_id': config_ui['slave_id'],
                        'address': address,
                        'data_type': config_ui['data_type_var'].get(),
                        'name': config_ui['name_entry'].get()
                    })
                except ValueError:
                    continue

        # Update status label
        count = len(self.modbus_configs)
        if count > 0:
            self.modbus_status_label.config(
                text=f"{count} ModBus address(es) configured", fg='green'
            )
        else:
            self.modbus_status_label.config(
                text="No ModBus addresses configured", fg='gray'
            )

        dialog.destroy()

    def _create_channel_section(self, parent: tk.Frame) -> None:
        """Create channel configuration section with signal conditioning."""
        frame = tk.LabelFrame(parent, text="Channel Configuration", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # Create scrollable frame for channels
        canvas = tk.Canvas(frame, height=200)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Header
        tk.Label(scrollable_frame, text="Channel", width=10).grid(row=0, column=0, padx=3)
        tk.Label(scrollable_frame, text="Name", width=15).grid(row=0, column=1, padx=3)
        tk.Label(scrollable_frame, text="Zero", width=8).grid(row=0, column=2, padx=3)
        tk.Label(scrollable_frame, text="Multiplier", width=10).grid(row=0, column=3, padx=3)
        tk.Label(scrollable_frame, text="Gain", width=8).grid(row=0, column=4, padx=3)
        tk.Label(scrollable_frame, text="Current Value", width=12).grid(row=0, column=5, padx=3)

        # Create channel configuration rows
        for i in range(self.channel_count):
            # Channel number
            tk.Label(scrollable_frame, text=f"Ch {i+1}").grid(row=i+1, column=0, padx=3, pady=2)

            # Name entry
            entry = tk.Entry(scrollable_frame, width=15)
            entry.grid(row=i+1, column=1, padx=3, pady=2)
            entry.insert(0, f"Channel_{i+1}")
            self.channel_entries.append(entry)

            # Zero offset
            zero_entry = tk.Entry(scrollable_frame, textvariable=self.channel_zero[i], width=8)
            zero_entry.grid(row=i+1, column=2, padx=3, pady=2)

            # Multiplier
            mult_entry = tk.Entry(scrollable_frame, textvariable=self.channel_multiplier[i], width=10)
            mult_entry.grid(row=i+1, column=3, padx=3, pady=2)

            # Gain
            gain_entry = tk.Entry(scrollable_frame, textvariable=self.channel_gain[i], width=8)
            gain_entry.grid(row=i+1, column=4, padx=3, pady=2)

            # Value display
            value_label = tk.Label(
                scrollable_frame, text="--", width=12,
                relief=tk.SUNKEN, bg='white',
                font=('Arial', 9, 'bold')
            )
            value_label.grid(row=i+1, column=5, padx=3, pady=2)
            self.channel_value_labels.append(value_label)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_control_section(self, parent: tk.Frame) -> None:
        """Create acquisition control section."""
        frame = tk.LabelFrame(parent, text="Acquisition Control", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # CSV filename input
        filename_frame = tk.Frame(frame)
        filename_frame.pack(pady=5)
        tk.Label(filename_frame, text="CSV Filename (optional):").pack(side=tk.LEFT, padx=5)
        filename_entry = tk.Entry(filename_frame, textvariable=self.csv_filename_var, width=30)
        filename_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(filename_frame, text=".csv", fg='gray').pack(side=tk.LEFT)

        # Control buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)

        self.start_btn = tk.Button(
            btn_frame, text="Start Acquisition",
            command=self._on_start_acquisition,
            width=20, state=tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_frame, text="Stop Acquisition",
            command=self._on_stop_acquisition,
            width=20, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Plot controls
        plot_btn_frame = tk.Frame(frame)
        plot_btn_frame.pack(pady=5)

        self.print_plot_btn = tk.Button(
            plot_btn_frame, text="Print Plot",
            command=self._on_print_plot,
            width=15
        )
        self.print_plot_btn.pack(side=tk.LEFT, padx=5)

        self.save_plot_btn = tk.Button(
            plot_btn_frame, text="Save Plot",
            command=self._on_save_plot,
            width=15
        )
        self.save_plot_btn.pack(side=tk.LEFT, padx=5)

        self.config_plot_btn = tk.Button(
            plot_btn_frame, text="Configure Plot",
            command=self._on_configure_plot,
            width=15
        )
        self.config_plot_btn.pack(side=tk.LEFT, padx=5)

        # Window management controls
        window_btn_frame = tk.Frame(frame)
        window_btn_frame.pack(pady=5)

        self.show_numeric_btn = tk.Button(
            window_btn_frame, text="Show Numeric Display",
            command=self._on_show_numeric_window,
            width=20
        )
        self.show_numeric_btn.pack(side=tk.LEFT, padx=5)

    def _create_plot_section(self, parent: tk.Frame) -> None:
        """Create plot section with embedded plot."""
        frame = tk.LabelFrame(parent, text="Real-Time Plot", padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create embedded PlotManager
        channel_names = [f"Channel_{i+1}" for i in range(self.channel_count)]
        self.plot_manager = PlotManager(frame, self.channel_count, channel_names)
        self.plot_manager.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_log_section(self, parent: tk.Frame) -> None:
        """Create log section."""
        frame = tk.LabelFrame(parent, text="Activity Log", padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(frame, height=8, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log_message(self, message: str) -> None:
        """
        Log a message to the activity log.

        Args:
            message: Message to log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def _on_connect(self) -> None:
        """Handle connection button click."""
        conn_type = self.conn_type.get()
        port = self.port_combo.get()

        if port == 'No ports found':
            self.ui_manager.show_error("Error", "No serial ports available")
            return

        try:
            baudrate = int(self.baudrate_entry.get())
        except ValueError:
            self.ui_manager.show_error("Error", "Invalid baudrate")
            return

        try:
            if conn_type == "Serial":
                self.serial_handler.connect(port, baudrate)
                self._log_message(f"Connected to {port} (Serial)")
            else:  # ModBus
                self.modbus_handler.connect(port, baudrate)
                self._log_message(f"Connected to {port} (ModBus)")

            self.ui_manager.update_status(self.status_label, "Connected", "green")
            self.connect_btn.config(text="Disconnect", command=self._on_disconnect)
            self.start_btn.config(state=tk.NORMAL)

        except ConnectionError as e:
            self.ui_manager.show_error("Connection Error", str(e))
            self._log_message(f"Connection failed: {str(e)}")

    def _on_disconnect(self) -> None:
        """Handle disconnect button click."""
        if self.acquisition_active:
            self._on_stop_acquisition()

        self.serial_handler.disconnect()
        self.modbus_handler.disconnect()

        self.ui_manager.update_status(self.status_label, "Disconnected", "red")
        self.connect_btn.config(text="Connect", command=self._on_connect)
        self.start_btn.config(state=tk.DISABLED)
        self._log_message("Disconnected")

    def _on_start_acquisition(self) -> None:
        """Handle start acquisition button click."""
        if self.acquisition_active:
            return

        # Get channel names
        channel_names = [entry.get() for entry in self.channel_entries]

        # Get custom filename if provided
        custom_filename = self.csv_filename_var.get().strip() or None

        # Start logging
        self.data_logger.start_logging(channel_names, custom_filename)

        # Start acquisition thread
        self.acquisition_active = True
        self.acquisition_thread = threading.Thread(
            target=self._acquisition_loop,
            daemon=True
        )
        self.acquisition_thread.start()

        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._log_message("Data acquisition started")
        if custom_filename:
            self._log_message(f"Logging to: {custom_filename}")

    def _on_stop_acquisition(self) -> None:
        """Handle stop acquisition button click."""
        if not self.acquisition_active:
            return

        self.acquisition_active = False

        # Wait for thread to finish
        if self.acquisition_thread:
            self.acquisition_thread.join(timeout=2)

        # Stop logging
        self.data_logger.stop_logging()

        # Update UI
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._log_message("Data acquisition stopped")

    def _acquisition_loop(self) -> None:
        """Main data acquisition loop (runs in separate thread)."""
        while self.acquisition_active:
            try:
                # Read raw data from configured sources
                raw_data = self._read_data()

                if raw_data:
                    # Apply signal conditioning to each channel
                    conditioned_data = []
                    for i, raw_value in enumerate(raw_data):
                        try:
                            zero = float(self.channel_zero[i].get())
                            multiplier = float(self.channel_multiplier[i].get())
                            gain = float(self.channel_gain[i].get())
                            # Formula: Display = (Raw + Zero) × Multiplier × Gain
                            conditioned_value = (raw_value + zero) * multiplier * gain
                            conditioned_data.append(conditioned_value)
                        except (ValueError, IndexError):
                            # If parameters invalid, use raw value
                            conditioned_data.append(raw_value)

                    # Log conditioned data
                    self.data_logger.log_data(conditioned_data)

                    # Update plot (on main thread)
                    if self.plot_manager:
                        self.root.after(0, lambda d=conditioned_data: self.plot_manager.update_data(d))

                    # Update numeric displays (on main thread)
                    self.root.after(0, lambda d=conditioned_data: self._update_numeric_displays(d))

                time.sleep(0.1)  # Acquisition rate

            except Exception as e:
                self._log_message(f"Acquisition error: {str(e)}")
                time.sleep(1)

    def _update_numeric_displays(self, data: List[float]) -> None:
        """Update numeric value displays in all windows."""
        # Update main window displays
        for i, value in enumerate(data):
            if i < len(self.channel_value_labels):
                self.channel_value_labels[i].config(text=f"{value:.2f}")

        # Update numeric display window
        if self.numeric_display_window and self.numeric_display_window.is_visible:
            for i, value in enumerate(data):
                self.numeric_display_window.update_value(i, value)

    def _read_data(self) -> List[float]:
        """
        Read data from connected device.

        Returns:
            List of channel values
        """
        # If ModBus is configured and connected, read from ModBus
        if self.modbus_configs and self.modbus_handler.is_connected:
            modbus_data = self.modbus_handler.read_multiple_addresses(self.modbus_configs)
            # Convert to list in order of configuration
            configs = self.modbus_configs[:self.channel_count]
            data = [modbus_data.get(cfg['name'], 0.0) for cfg in configs]
            # Pad with zeros if needed
            while len(data) < self.channel_count:
                data.append(0.0)
            return data[:self.channel_count]

        # Otherwise, use simulated data for demonstration
        # TODO: Replace with actual serial_handler.read() for serial communication
        return [random.uniform(0, 100) for _ in range(self.channel_count)]

    def _on_print_plot(self) -> None:
        """Handle print plot button click."""
        try:
            if self.plot_manager and self.plot_manager.figure:
                from matplotlib.backends.backend_pdf import PdfPages
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp_path = tmp.name
                with PdfPages(tmp_path) as pdf:
                    pdf.savefig(self.plot_manager.figure)
                import platform
                if platform.system() == 'Windows':
                    os.startfile(tmp_path, 'print')
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open {tmp_path}')
                else:  # Linux
                    os.system(f'xdg-open {tmp_path}')
                self._log_message("Plot sent to printer")
            else:
                self.ui_manager.show_info("No Plot", "No plot data available.")
        except Exception as e:
            self.ui_manager.show_error("Print Error", f"Failed to print plot: {str(e)}")
            self._log_message(f"Print error: {str(e)}")

    def _on_save_plot(self) -> None:
        """Handle save plot button click."""
        try:
            if not self.plot_manager or not self.plot_manager.figure:
                self.ui_manager.show_info("No Plot", "No plot data available.")
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.plot_manager.figure.savefig(filename, dpi=300, bbox_inches='tight')
                self._log_message(f"Plot saved to {filename}")
                self.ui_manager.show_info("Success", "Plot saved successfully")
        except Exception as e:
            self.ui_manager.show_error("Save Error", f"Failed to save plot: {str(e)}")
            self._log_message(f"Save error: {str(e)}")

    def _on_configure_plot(self) -> None:
        """Handle configure plot button click."""
        if not self.plot_manager:
            self.ui_manager.show_info("No Plot", "No plot available.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Plot")
        dialog.geometry("400x250")

        # Title
        tk.Label(dialog, text="Plot Title:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        title_entry = tk.Entry(dialog, width=30)
        title_entry.grid(row=0, column=1, padx=10, pady=10)
        title_entry.insert(0, "Data Acquisition - All Channels")

        # X Label
        tk.Label(dialog, text="X-axis Label:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        xlabel_entry = tk.Entry(dialog, width=30)
        xlabel_entry.grid(row=1, column=1, padx=10, pady=10)
        xlabel_entry.insert(0, "Sample")

        # Y Label
        tk.Label(dialog, text="Y-axis Label:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        ylabel_entry = tk.Entry(dialog, width=30)
        ylabel_entry.grid(row=2, column=1, padx=10, pady=10)
        ylabel_entry.insert(0, "Value")

        # Grid option
        grid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="Show Grid", variable=grid_var).grid(
            row=3, column=0, columnspan=2, pady=10
        )

        # Apply button
        def apply_config():
            self.plot_manager.configure_plot(
                title_entry.get(),
                xlabel_entry.get(),
                ylabel_entry.get(),
                grid_var.get()
            )
            self._log_message("Plot configuration updated")
            dialog.destroy()

        tk.Button(dialog, text="Apply", command=apply_config, width=15).grid(
            row=4, column=0, columnspan=2, pady=10
        )

    def _on_show_numeric_window(self) -> None:
        """Show the numeric display window."""
        channel_names = [entry.get() for entry in self.channel_entries]
        self.numeric_display_window.show(self.root, channel_names)
        self._log_message("Numeric display window shown")

    def _on_closing(self) -> None:
        """Handle window close event."""
        if self.acquisition_active:
            self._on_stop_acquisition()

        # Close numeric display window
        if self.numeric_display_window:
            self.numeric_display_window.close()

        self.serial_handler.disconnect()
        self.modbus_handler.disconnect()

        self.root.destroy()

    def run(self) -> None:
        """Start the application main loop."""
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DASSApplication(root)
    app.run()


if __name__ == "__main__":
    main()

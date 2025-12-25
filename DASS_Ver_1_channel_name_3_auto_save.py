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
    from tkinter import ttk, scrolledtext, messagebox
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
DEFAULT_CHANNEL_COUNT = 3
MAX_DATA_POINTS = 100
LOG_DIRECTORY = "logs"


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

    def start_logging(self, channel_names: List[str]) -> None:
        """
        Start logging with specified channel names.

        Args:
            channel_names: List of channel names for CSV header
        """
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


class PlotManager:
    """
    Manages real-time plotting of data channels.
    Handles multiple channels with automatic color assignment.
    """

    def __init__(self, parent_frame: tk.Frame, channel_count: int):
        """
        Initialize the plot manager.

        Args:
            parent_frame: Tkinter frame to embed the plot
            channel_count: Number of data channels to plot
        """
        self.channel_count = channel_count
        self.data_buffers: List[List[float]] = [[] for _ in range(channel_count)]

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.lines: List[Any] = []

        # Initialize plot lines
        colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        for i in range(channel_count):
            color = colors[i % len(colors)]
            line, = self.ax.plot([], [], f'{color}-', label=f'Channel {i+1}')
            self.lines.append(line)

        self.ax.set_xlabel('Sample')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Real-time Data Plot')
        self.ax.legend()
        self.ax.grid(True)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_data(self, channel_index: int, value: float) -> None:
        """
        Update data for a specific channel.

        Args:
            channel_index: Index of the channel
            value: New data value
        """
        if 0 <= channel_index < self.channel_count:
            buffer = self.data_buffers[channel_index]
            buffer.append(value)

            # Keep only recent data points
            if len(buffer) > MAX_DATA_POINTS:
                buffer.pop(0)

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

    def _create_channel_section(self, parent: tk.Frame) -> None:
        """Create channel configuration section."""
        frame = tk.LabelFrame(parent, text="Channel Configuration", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # Create channel name entries
        for i in range(self.channel_count):
            entry = self.ui_manager.create_labeled_entry(
                frame, f"Channel {i+1} Name:", i, default=f"Channel_{i+1}"
            )
            self.channel_entries.append(entry)

    def _create_control_section(self, parent: tk.Frame) -> None:
        """Create acquisition control section."""
        frame = tk.LabelFrame(parent, text="Acquisition Control", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # Control buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack()

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

    def _create_plot_section(self, parent: tk.Frame) -> None:
        """Create plot section."""
        frame = tk.LabelFrame(parent, text="Real-time Plot", padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.plot_manager = PlotManager(frame, self.channel_count)

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

        # Start logging
        self.data_logger.start_logging(channel_names)

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
                # Simulate data acquisition
                # In real implementation, read from serial/ModBus
                data = self._read_data()

                if data:
                    # Log data
                    self.data_logger.log_data(data)

                    # Update plot
                    for i, value in enumerate(data):
                        self.plot_manager.update_data(i, value)

                    # Refresh plot (on main thread)
                    self.root.after(0, self.plot_manager.refresh_plot)

                time.sleep(0.1)  # Acquisition rate

            except Exception as e:
                self._log_message(f"Acquisition error: {str(e)}")
                time.sleep(1)

    def _read_data(self) -> List[float]:
        """
        Read data from connected device.

        Returns:
            List of channel values
        """
        # TODO: Replace with actual device reading implementation
        # For now, returns simulated data for demonstration purposes
        # In production, replace with:
        #   - serial_handler.read() for serial communication
        #   - modbus_handler.read_holding_registers() for ModBus devices
        return [random.uniform(0, 100) for _ in range(self.channel_count)]

    def _on_closing(self) -> None:
        """Handle window close event."""
        if self.acquisition_active:
            self._on_stop_acquisition()

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

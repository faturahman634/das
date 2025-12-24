import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser, filedialog
import os
import json
import csv
import struct
import time
import threading
import re
from datetime import datetime
from collections import deque

import serial
import serial.tools.list_ports
from pymodbus.client.sync import ModbusSerialClient

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backends.backend_pdf import PdfPages

# =========================================================
# --------------------- Constants -------------------------
# =========================================================

SETTINGS_FILE = "adm4280_settings.json"
DATA_SOURCE_MODBUS = "Modbus"
DATA_SOURCE_SERIAL = "Serial"
DATA_SOURCE_ACTIVE_SERIAL = "Active Serial"

ENCODER_CHANNEL_NAME = "Encoder"
MAX_PLOT_CHANNELS = 6
NUMERIC_DISPLAY_COUNT = 6

TIME_OPTIONS = [
    ("1 minute", 60),
    ("5 minutes", 5 * 60),
    ("10 minutes", 10 * 60),
    ("30 minutes", 30 * 60),
    ("1 hour", 60 * 60),
    ("2 hours", 2 * 60 * 60),
    ("3 hours", 3 * 60 * 60),
    ("5 hours", 5 * 60 * 60),
    ("10 hours", 10 * 60 * 60),
]

DEFAULT_PLOT_COLORS = [
    "#0072bd", "#d95319", "#edb120", "#7e2f8e", "#77ac30", "#4dbeee"
]

# =========================================================
# ------------------- Global Variables --------------------
# =========================================================

# Flags
reading_active = False
logging_active = False

# Logging handles
logged_filename = None
csv_writer = None
csv_file_handle = None
fields = []

# Modbus Client
client = None

# Plot config
plot_data_deques = [deque() for _ in range(MAX_PLOT_CHANNELS)]
plot_paused = False
plot_pointer_line = None
plot_pointer_text = None
plot_persistent_pointer_line = None
plot_persistent_pointer_text = None

# Total rate/volume channel selection
total_rate_channels_var = []
total_volume_channels_var = []

# ===========...
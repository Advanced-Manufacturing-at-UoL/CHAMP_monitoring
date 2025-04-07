from pathlib import Path
from enum import Enum

ROOT_DIR = Path.home() / "rootdir"
ARDUINO_PORT = "COM4"
ARDUINO_BAUD = 9600

class DataTypes(Enum):
    PRESSURE = "Pressure"
    LASER = "Laser"
    CAMERA = "Camera"

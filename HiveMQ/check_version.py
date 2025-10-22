import sys
import importlib.metadata

print("Python executable:", sys.executable)

try:
    version = importlib.metadata.version('paho-mqtt')
except importlib.metadata.PackageNotFoundError:
    version = "paho-mqtt not found"

print("paho-mqtt version:", version)

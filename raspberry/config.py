import os

# --- Sensor Identity ---
ROOM_ID   = os.getenv("ROOM_ID",   "room-01")
SENSOR_ID = os.getenv("SENSOR_ID", "sensor-01")

# --- Serial ---
SERIAL_CFG_PORT  = os.getenv("SERIAL_CFG_PORT",  "/dev/ttyUSB0")
SERIAL_DATA_PORT = os.getenv("SERIAL_DATA_PORT", "/dev/ttyUSB1")
SERIAL_CFG_BAUD  = 115200
SERIAL_DATA_BAUD = 921600

# --- Backend WebSocket ---
BACKEND_HOST    = os.getenv("BACKEND_HOST",    "localhost")
BACKEND_PORT    = os.getenv("BACKEND_PORT",    "8000")
BACKEND_WS_PATH = os.getenv("BACKEND_WS_PATH", "/ws/occupancy")
BACKEND_WS_URL  = f"ws://{BACKEND_HOST}:{BACKEND_PORT}{BACKEND_WS_PATH}"

# --- WebSocket Reconnect ---
WS_RECONNECT_DELAY = 5  # seconds until next try
WS_MAX_RETRIES     = 0  # 0 = infinite retries
import serial
import os
import logging
import sys
import struct

from requests.compat import integer_types

# Configuration for the AOP 6m sensor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "chirp_configs", "AOP_6m_default.cfg")

# Serial port settings (adjust as needed for system)
# COM Ports are the actual physical ports on your device
# BAUD -> how many bits are transferred per second. Needs to be on receiver and sender the same

CFG_PORT = "COM3"
DATA_PORT = "COM4"
CFG_BAUD = 115200
DATA_BAUD = 921600

MAGIC_WORD = b'\x02\x01\x04\x03\x06\x05\x08\x07'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stdout)
log = logging.getLogger(__name__)


# Open the serial ports for configuration and data
def open_ports():
    cfg_port = serial.Serial(CFG_PORT, CFG_BAUD, timeout=1)
    data_port = serial.Serial(DATA_PORT, DATA_BAUD, timeout=1)
    return cfg_port, data_port

# Send the configuration commands from the file to the sensor and read responses
def send_config(cfg_port, config_file):
    with open(config_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('%') or line.strip() == "":
                continue
            cfg_port.write((line.strip() + '\n').encode())

            response = ""
            while True:
                resp_line = cfg_port.readline().decode()
                response += resp_line
                if 'Done' in resp_line or 'Error' in resp_line:
                    break
                if resp_line.strip() == '':
                    break

            log.info(f"Sent: {line.strip()} | Response: {response.strip()}")

def read_frame(data_port):
        buffer = bytearray()
        while True:
                byte = data_port.read(1)
                buffer += byte
                if buffer[-8:] == MAGIC_WORD:
                    print("Magic word found")

                    # Empty buffer to save memory
                    buffer = bytearray()

                    header_bytes = data_port.read(32)
                    (version,
                     total_length,
                     platform,
                     frame_num,
                     time_cpu,
                     num_detected,
                     num_tlvs,
                     sub_frame) = struct.unpack('8I', header_bytes)

# Main execution
if __name__ == '__main__':
    cfg_port = None
    data_port = None
    try:
        cfg_port, data_port = open_ports()
        send_config(cfg_port, CONFIG_FILE)
    except serial.SerialException as e:
        log.error(f"Error: Couldn't find sensor. {e}")
    finally:
        if cfg_port:
            cfg_port.close()
        if data_port:
            data_port.close()
import serial
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "chirp_configs", "AOP_6m_default.cfg")

CFG_PORT = "COM3"
DATA_PORT = "COM4"
CFG_BAUD = 115200
DATA_BAUD = 921600



def open_ports():
    cfg_port = serial.Serial(CFG_PORT, CFG_BAUD, timeout=1)
    data_port = serial.Serial(DATA_PORT, DATA_BAUD, timeout=1)
    return cfg_port, data_port

def send_config(cfg_port, config_file):
    with open(config_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('%') or line.strip() == "":
                continue
            else:
                cfg_port.write((line.strip() + '\n').encode())
                response = cfg_port.readline().decode()
                print(f"Sent: {line.strip()} | Response: {response.strip()}")

if __name__ == '__main__':
    try:
        cfg_port, data_port = open_ports()
        send_config(cfg_port, CONFIG_FILE)
    except serial.SerialException as e:
        print(f"Error: Couldn't find sensor. {e}")
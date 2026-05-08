from sensor.receiver import *

# Main execution
if __name__ == '__main__':
    cfg_port = None
    data_port = None
    try:
        cfg_port, data_port = open_ports()
        send_config(cfg_port, CONFIG_FILE)

        while True:
            frame_num, people_count = read_frame(data_port)
            log.info(f"Frame {frame_num}: Detected {people_count} people")
    except serial.SerialException as e:
        log.error(f"Error: Couldn't find sensor. {e}")
    finally:
        if cfg_port:
            cfg_port.close()
        if data_port:
            data_port.close()
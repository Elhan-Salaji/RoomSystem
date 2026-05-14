import logging
import time


log = logging.getLogger(__name__)

def mock_sensor_loop(enqueue_frame):
    """Sends 10 mock frames for testing."""
    for frame_num in range(1, 11):
        people_count = frame_num % 3  # 0, 1, 2, 0, 1, 2 ...
        log.info(f"Frame {frame_num}: Detected {people_count} people")
        enqueue_frame({"frameNum": frame_num, "numDetectedTracks": people_count})
        time.sleep(0.1)
    log.info("Mock done — 10 frames sent.")
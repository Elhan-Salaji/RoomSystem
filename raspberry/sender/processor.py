from datetime import datetime, timezone
from config import ROOM_ID, SENSOR_ID

def map_to_occupancy(frame: dict) -> dict:
    """
    Mapped einen geparsten mmWave-Frame auf das OccupancyData-Modell.
    Args:
        frame: Dict mit mindestens 'numDetectedTracks' und 'frameNum'

    Returns:
        OccupancyData als Dict (JSON-serialisierbar)
    """
    return {
        "roomId":     ROOM_ID,
        "sensorId":   SENSOR_ID,
        "count":      frame.get("numDetectedTracks", 0),
        "confidence": 1.0,   # Platzhalter – später durch echte Logik ersetzen
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
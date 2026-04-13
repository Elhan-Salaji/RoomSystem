package com.roomsystem.feature.receiver;

import com.roomsystem.feature.receiver.dto.SensorData;

public interface SensorDataService {
    void process(SensorData data);
}

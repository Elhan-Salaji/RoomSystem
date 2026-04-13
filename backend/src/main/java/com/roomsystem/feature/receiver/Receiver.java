package com.roomsystem.feature.receiver;

import com.roomsystem.feature.receiver.dto.SensorData;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;

@Controller
public class Receiver {

    private final SensorDataService sensorDataService;

    public Receiver(SensorDataService sensorDataService) {
        this.sensorDataService = sensorDataService;
    }

    @MessageMapping("/data")
    public void receive(SensorData data) {
        if (data == null) return;
        sensorDataService.process(data);
    }
}

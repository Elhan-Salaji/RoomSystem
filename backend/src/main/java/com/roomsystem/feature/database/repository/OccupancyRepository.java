package com.roomsystem.feature.database.repository;

import com.influxdb.v3.client.InfluxDBClient;
import com.influxdb.v3.client.Point;
import com.roomsystem.feature.database.model.OccupancyData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

/**
 * Repository for persisting anonymized occupancy measurements to InfluxDB 3.x.
 * Only stores processed headcounts — never raw sensor data.
 */
@Slf4j
@Repository
@RequiredArgsConstructor
public class OccupancyRepository {

    static final String MEASUREMENT_NAME = "occupancy";

    private final InfluxDBClient influxDBClient;

    /**
     * Saves a single occupancy measurement to InfluxDB.
     * Assigns the current timestamp if none is set.
     *
     * @param data the occupancy measurement to persist
     * @throws IllegalArgumentException if data is null or has invalid fields
     */
    public void save(OccupancyData data) {
        validate(data);
        assignTimestampIfMissing(data);

        Point point = toPoint(data);
        influxDBClient.writePoint(point);

        log.debug("Saved occupancy data: room={}, count={}, ts={}",
                data.getRoomId(), data.getCount(), data.getTimestamp());
    }

    /**
     * Saves a batch of occupancy measurements in a single write operation.
     *
     * @param batch the list of occupancy measurements to persist
     * @throws IllegalArgumentException if batch is null or empty
     */
    public void saveBatch(List<OccupancyData> batch) {
        if (batch == null || batch.isEmpty()) {
            throw new IllegalArgumentException("Batch must not be null or empty");
        }

        batch.forEach(this::validate);
        batch.forEach(this::assignTimestampIfMissing);

        List<Point> points = batch.stream()
                .map(this::toPoint)
                .toList();

        influxDBClient.writePoints(points);

        log.debug("Saved batch of {} occupancy measurements", batch.size());
    }

    /**
     * Converts an OccupancyData object to an InfluxDB Point.
     */
    private Point toPoint(OccupancyData data) {
        return Point.measurement(MEASUREMENT_NAME)
                .setTag("roomId", data.getRoomId())
                .setTag("sensorId", data.getSensorId())
                .setIntegerField("count", data.getCount())
                .setFloatField("confidence", data.getConfidence())
                .setTimestamp(data.getTimestamp());
    }

    private void validate(OccupancyData data) {
        if (data == null) {
            throw new IllegalArgumentException("OccupancyData must not be null");
        }
        if (data.getRoomId() == null || data.getRoomId().isBlank()) {
            throw new IllegalArgumentException("roomId must not be null or blank");
        }
        if (data.getSensorId() == null || data.getSensorId().isBlank()) {
            throw new IllegalArgumentException("sensorId must not be null or blank");
        }
        if (data.getCount() < 0) {
            throw new IllegalArgumentException("count must not be negative");
        }
        if (data.getConfidence() < 0.0 || data.getConfidence() > 1.0) {
            throw new IllegalArgumentException("confidence must be between 0.0 and 1.0");
        }
    }

    private void assignTimestampIfMissing(OccupancyData data) {
        if (data.getTimestamp() == null) {
            data.setTimestamp(Instant.now());
        }
    }
}

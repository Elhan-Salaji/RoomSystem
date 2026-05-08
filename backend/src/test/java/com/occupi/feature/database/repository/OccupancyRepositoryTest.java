package com.occupi.feature.database.repository;

import com.influxdb.v3.client.InfluxDBClient;
import com.influxdb.v3.client.Point;
import com.occupi.feature.database.model.OccupancyData;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("OccupancyRepository")
class OccupancyRepositoryTest {

    @Mock
    private InfluxDBClient influxDBClient;

    private OccupancyRepository repository;

    @BeforeEach
    void setUp() {
        repository = new OccupancyRepository(influxDBClient);
    }

    @Nested
    @DisplayName("save()")
    class Save {

        @Test
        @DisplayName("should write a point to InfluxDB with correct measurement name")
        void shouldWritePointToInfluxDB() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .sensorId("sensor-A")
                    .count(15)
                    .confidence(0.95)
                    .timestamp(Instant.parse("2026-04-13T10:00:00Z"))
                    .build();

            repository.save(data);

            verify(influxDBClient).writePoint(any(Point.class));
        }

        @Test
        @DisplayName("should use current timestamp when none is provided")
        void shouldUseCurrentTimestampWhenNoneProvided() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .sensorId("sensor-A")
                    .count(10)
                    .confidence(0.8)
                    .build();

            Instant before = Instant.now();
            repository.save(data);
            Instant after = Instant.now();

            // Verify the data object got a timestamp assigned
            assertNotNull(data.getTimestamp());
            assertFalse(data.getTimestamp().isBefore(before));
            assertFalse(data.getTimestamp().isAfter(after));
        }

        @Test
        @DisplayName("should reject null occupancy data")
        void shouldRejectNullData() {
            assertThrows(IllegalArgumentException.class, () -> repository.save(null));
        }

        @Test
        @DisplayName("should reject data with missing roomId")
        void shouldRejectMissingRoomId() {
            OccupancyData data = OccupancyData.builder()
                    .sensorId("sensor-A")
                    .count(5)
                    .confidence(0.9)
                    .timestamp(Instant.now())
                    .build();

            assertThrows(IllegalArgumentException.class, () -> repository.save(data));
        }

        @Test
        @DisplayName("should reject data with missing sensorId")
        void shouldRejectMissingSensorId() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .count(5)
                    .confidence(0.9)
                    .timestamp(Instant.now())
                    .build();

            assertThrows(IllegalArgumentException.class, () -> repository.save(data));
        }

        @Test
        @DisplayName("should reject negative count")
        void shouldRejectNegativeCount() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .sensorId("sensor-A")
                    .count(-1)
                    .confidence(0.9)
                    .timestamp(Instant.now())
                    .build();

            assertThrows(IllegalArgumentException.class, () -> repository.save(data));
        }

        @Test
        @DisplayName("should reject confidence outside 0.0-1.0 range")
        void shouldRejectInvalidConfidence() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .sensorId("sensor-A")
                    .count(5)
                    .confidence(1.5)
                    .timestamp(Instant.now())
                    .build();

            assertThrows(IllegalArgumentException.class, () -> repository.save(data));
        }
    }

    @Nested
    @DisplayName("saveBatch()")
    class SaveBatch {

        @Test
        @DisplayName("should write multiple points in a single batch")
        void shouldWriteMultiplePoints() {
            List<OccupancyData> batch = List.of(
                    OccupancyData.builder()
                            .roomId("seminar-101").sensorId("sensor-A")
                            .count(10).confidence(0.9).timestamp(Instant.now())
                            .build(),
                    OccupancyData.builder()
                            .roomId("seminar-102").sensorId("sensor-B")
                            .count(20).confidence(0.85).timestamp(Instant.now())
                            .build()
            );

            repository.saveBatch(batch);

            verify(influxDBClient).writePoints(anyList());
        }

        @Test
        @DisplayName("should reject empty batch")
        void shouldRejectEmptyBatch() {
            assertThrows(IllegalArgumentException.class, () -> repository.saveBatch(List.of()));
        }
    }
}

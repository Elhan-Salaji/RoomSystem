package com.roomsystem.feature.receiver;

import com.roomsystem.feature.database.model.OccupancyData;
import com.roomsystem.feature.database.service.OccupancyService;
import com.roomsystem.feature.receiver.dto.SensorData;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

/**
 * Unit tests for {@link SensorDataServiceImpl}.
 *
 * Tests the mapping of {@link SensorData} to {@link OccupancyData}
 * and delegation to {@link OccupancyService}.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("SensorDataServiceImpl Tests")
class SensorDataServiceImplTest {

    @Mock
    private OccupancyService occupancyService;

    private SensorDataServiceImpl sensorDataService;

    @BeforeEach
    void setUp() {
        sensorDataService = new SensorDataServiceImpl(occupancyService);
    }

    @Test
    @DisplayName("Should map all SensorData fields to OccupancyData correctly")
    void testMappingAllFields() {
        // Arrange
        Instant timestamp = Instant.parse("2024-01-15T10:30:00Z");
        SensorData sensorData = new SensorData(
                "seminar-101",
                "sensor-A",
                5,
                0.95,
                timestamp
        );

        // Act
        sensorDataService.process(sensorData);

        // Assert
        ArgumentCaptor<OccupancyData> captor = ArgumentCaptor.forClass(OccupancyData.class);
        verify(occupancyService).recordOccupancy(captor.capture());

        OccupancyData captured = captor.getValue();
        assertThat(captured)
                .extracting(
                        OccupancyData::getRoomId,
                        OccupancyData::getSensorId,
                        OccupancyData::getCount,
                        OccupancyData::getConfidence,
                        OccupancyData::getTimestamp
                )
                .containsExactly(
                        "seminar-101",
                        "sensor-A",
                        5,
                        0.95,
                        timestamp
                );
    }

    @Test
    @DisplayName("Should delegate to OccupancyService.recordOccupancy()")
    void testDelegationToOccupancyService() {
        // Arrange
        SensorData sensorData = new SensorData(
                "room-202",
                "sensor-B",
                8,
                0.87,
                Instant.now()
        );

        // Act
        sensorDataService.process(sensorData);

        // Assert
        verify(occupancyService).recordOccupancy(org.mockito.ArgumentMatchers.any(OccupancyData.class));
    }

    @Test
    @DisplayName("Should handle null SensorData gracefully")
    void testHandleNullSensorData() {
        // Act
        sensorDataService.process(null);

        // Assert
        verify(occupancyService, never()).recordOccupancy(org.mockito.ArgumentMatchers.any());
    }

    @Test
    @DisplayName("Should propagate exceptions from OccupancyService")
    void testExceptionPropagation() {
        // Arrange
        SensorData sensorData = new SensorData(
                "room-101",
                "sensor-A",
                3,
                0.92,
                Instant.now()
        );
        org.mockito.Mockito.doThrow(new RuntimeException("Database connection failed"))
                .when(occupancyService).recordOccupancy(org.mockito.ArgumentMatchers.any());

        // Act & Assert
        assertThatThrownBy(() -> sensorDataService.process(sensorData))
                .isInstanceOf(RuntimeException.class)
                .hasMessage("Database connection failed");
    }

    @Test
    @DisplayName("Should handle edge case: confidence at boundaries")
    void testConfidenceBoundaryValues() {
        // Arrange - Test confidence = 0.0
        SensorData lowConfidence = new SensorData(
                "room-101",
                "sensor-A",
                0,
                0.0,
                Instant.now()
        );

        // Act
        sensorDataService.process(lowConfidence);

        // Assert
        ArgumentCaptor<OccupancyData> captor = ArgumentCaptor.forClass(OccupancyData.class);
        verify(occupancyService).recordOccupancy(captor.capture());
        assertThat(captor.getValue().getConfidence()).isEqualTo(0.0);

        // Arrange - Test confidence = 1.0
        org.mockito.Mockito.reset(occupancyService);
        SensorData highConfidence = new SensorData(
                "room-101",
                "sensor-A",
                10,
                1.0,
                Instant.now()
        );

        // Act
        sensorDataService.process(highConfidence);

        // Assert
        verify(occupancyService).recordOccupancy(captor.capture());
        assertThat(captor.getValue().getConfidence()).isEqualTo(1.0);
    }

    @Test
    @DisplayName("Should handle edge case: zero count")
    void testZeroCountScenario() {
        // Arrange
        SensorData sensorData = new SensorData(
                "room-101",
                "sensor-A",
                0,
                0.85,
                Instant.now()
        );

        // Act
        sensorDataService.process(sensorData);

        // Assert
        ArgumentCaptor<OccupancyData> captor = ArgumentCaptor.forClass(OccupancyData.class);
        verify(occupancyService).recordOccupancy(captor.capture());
        assertThat(captor.getValue().getCount()).isEqualTo(0);
    }

    @Test
    @DisplayName("Should handle edge case: large count values")
    void testLargeCountScenario() {
        // Arrange
        SensorData sensorData = new SensorData(
                "auditorium-001",
                "sensor-master",
                1000,
                0.99,
                Instant.now()
        );

        // Act
        sensorDataService.process(sensorData);

        // Assert
        ArgumentCaptor<OccupancyData> captor = ArgumentCaptor.forClass(OccupancyData.class);
        verify(occupancyService).recordOccupancy(captor.capture());
        assertThat(captor.getValue().getCount()).isEqualTo(1000);
    }

    @Test
    @DisplayName("Should handle multiple consecutive calls")
    void testMultipleConsecutiveCalls() {
        // Arrange
        SensorData data1 = new SensorData("room-101", "sensor-A", 5, 0.9, Instant.now());
        SensorData data2 = new SensorData("room-102", "sensor-B", 3, 0.85, Instant.now());

        // Act
        sensorDataService.process(data1);
        sensorDataService.process(data2);

        // Assert
        verify(occupancyService, org.mockito.Mockito.times(2))
                .recordOccupancy(org.mockito.ArgumentMatchers.any());
    }
}

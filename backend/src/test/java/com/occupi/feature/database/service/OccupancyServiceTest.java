package com.occupi.feature.database.service;

import com.occupi.feature.database.model.OccupancyData;
import com.occupi.feature.database.repository.OccupancyRepository;
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
@DisplayName("OccupancyService")
class OccupancyServiceTest {

    @Mock
    private OccupancyRepository occupancyRepository;

    private OccupancyService service;

    @BeforeEach
    void setUp() {
        service = new OccupancyService(occupancyRepository);
    }

    @Nested
    @DisplayName("recordOccupancy()")
    class RecordOccupancy {

        @Test
        @DisplayName("should delegate to repository with correct data")
        void shouldDelegateToRepository() {
            OccupancyData data = OccupancyData.builder()
                    .roomId("seminar-101")
                    .sensorId("sensor-A")
                    .count(12)
                    .confidence(0.92)
                    .timestamp(Instant.now())
                    .build();

            service.recordOccupancy(data);

            ArgumentCaptor<OccupancyData> captor = ArgumentCaptor.forClass(OccupancyData.class);
            verify(occupancyRepository).save(captor.capture());

            OccupancyData saved = captor.getValue();
            assertEquals("seminar-101", saved.getRoomId());
            assertEquals("sensor-A", saved.getSensorId());
            assertEquals(12, saved.getCount());
            assertEquals(0.92, saved.getConfidence());
        }

        @Test
        @DisplayName("should propagate repository exceptions")
        void shouldPropagateExceptions() {
            doThrow(new IllegalArgumentException("invalid"))
                    .when(occupancyRepository).save(any());

            OccupancyData data = OccupancyData.builder().build();

            assertThrows(IllegalArgumentException.class,
                    () -> service.recordOccupancy(data));
        }
    }

    @Nested
    @DisplayName("recordBatch()")
    class RecordBatch {

        @Test
        @DisplayName("should delegate batch to repository")
        void shouldDelegateBatchToRepository() {
            List<OccupancyData> batch = List.of(
                    OccupancyData.builder()
                            .roomId("seminar-101").sensorId("sensor-A")
                            .count(10).confidence(0.9).timestamp(Instant.now())
                            .build(),
                    OccupancyData.builder()
                            .roomId("seminar-101").sensorId("sensor-B")
                            .count(12).confidence(0.88).timestamp(Instant.now())
                            .build()
            );

            service.recordBatch(batch);

            verify(occupancyRepository).saveBatch(batch);
        }
    }
}

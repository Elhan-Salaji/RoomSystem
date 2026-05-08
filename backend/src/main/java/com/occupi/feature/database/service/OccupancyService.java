package com.occupi.feature.database.service;

import com.occupi.feature.database.model.OccupancyData;
import com.occupi.feature.database.repository.OccupancyRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Service layer for occupancy data operations.
 * Coordinates between data receivers and the persistence layer.
 * Ensures only anonymized, processed headcounts are stored.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OccupancyService {

    private final OccupancyRepository occupancyRepository;

    /**
     * Records a single occupancy measurement.
     *
     * @param data the anonymized occupancy data from a sensor
     */
    public void recordOccupancy(OccupancyData data) {
        log.info("Recording occupancy: room={}, sensor={}, count={}",
                data.getRoomId(), data.getSensorId(), data.getCount());
        occupancyRepository.save(data);
    }

    /**
     * Records a batch of occupancy measurements in a single operation.
     *
     * @param batch the list of anonymized occupancy data points
     */
    public void recordBatch(List<OccupancyData> batch) {
        log.info("Recording batch of {} occupancy measurements", batch.size());
        occupancyRepository.saveBatch(batch);
    }
}

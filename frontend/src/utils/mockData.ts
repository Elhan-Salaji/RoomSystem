import type { Room, Forecast } from '../types/room';

export const MOCK_FORECASTS: Forecast[] = [
    { roomId: '016E', forecastTime: '14:00', predictedOccupancy: 45, probability: 0.85 },
    { roomId: '016E', forecastTime: '15:00', predictedOccupancy: 10, probability: 0.95 }, // Vorlesungsende?
];

export const MOCK_ROOMS: Room[] = [
    {
        id: '016E',
        name: 'Lernwelt',
        building: 'Hauptgebäude',
        floor: 0,
        currentOccupancy: 49,
        maxCapacity: 50,
        status: 'high',
        lastUpdate: new Date().toISOString(),
    },
    {
        id: '136',
        name: 'Poolraum',
        building: 'Hauptgebäude',
        floor: 1,
        currentOccupancy: 6,
        maxCapacity: 20,
        status: 'low',
        lastUpdate: new Date().toISOString(),
    },
    {
        id: 'I003',
        name: 'Audimax',
        building: 'Informationsgebäude',
        floor: -1,
        currentOccupancy: 110,
        maxCapacity: 250,
        status: 'medium',
        lastUpdate: new Date().toISOString(),
    }
];
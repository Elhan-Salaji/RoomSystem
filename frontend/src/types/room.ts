//Detaillierter als eine Zahl, was passiert im Moment
export interface Occupancy{
    roomId: string;
    timestamp: string;
    count: number;
}

//Was wird in Zukunft passieren?
export interface Forecast{
    roomId: string;
    forecastTime: string;
    predictedOccupancy: number;
    probability: number; //Algorithmus
}

export interface Room {
    id: string;
    name: string;
    building: string;
    floor: number;
    currentOccupancy: number; // How many people are in the room?
    maxCapacity: number;      // How many people can fit in the room?
    status: 'low' | 'medium' | 'high'; // status
    lastUpdate: string;       // timestamp of last update
}
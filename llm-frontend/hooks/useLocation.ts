import { useState, useEffect } from 'react';

export interface LocationData {
    latitude: number;
    longitude: number;
    accuracy?: number;
}

/**
 * Hook to get user's geolocation
 * Returns location data and ready state
 */
export function useLocation() {
    const [location, setLocation] = useState<LocationData | null>(null);
    const [locationReady, setLocationReady] = useState(false);

    useEffect(() => {
        let cancelled = false;
        setLocationReady(false);

        if (!('geolocation' in navigator)) {
            setLocation(null);
            setLocationReady(true);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (cancelled) return;
                setLocation({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                });
                setLocationReady(true);
            },
            (error) => {
                console.warn('Geolocation error:', error);
                if (cancelled) return;
                setLocation(null);
                setLocationReady(true);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );

        return () => {
            cancelled = true;
        };
    }, []);

    return { location, locationReady };
}

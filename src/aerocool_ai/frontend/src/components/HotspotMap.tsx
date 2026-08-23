import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Rectangle, Popup, useMap } from 'react-leaflet';
import { HotspotFeature } from '../types';

interface HotspotMapProps {
  bbox: [number, number, number, number];
  center: [number, number];
  hotspots: HotspotFeature[];
  mapTile: 'dark' | 'satellite' | 'street';
}

function ChangeMapView({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 13);
  }, [center, map]);
  return null;
}

export const HotspotMap: React.FC<HotspotMapProps> = ({
  bbox,
  center,
  hotspots,
  mapTile,
}) => {
  const tileUrls = {
    dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    street: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  };

  const bounds: [[number, number], [number, number]] = [
    [bbox[1], bbox[0]],
    [bbox[3], bbox[2]],
  ];

  return (
    <div className="w-full h-[520px] rounded-2xl overflow-hidden border border-slate-700/60 shadow-xl relative">
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <ChangeMapView center={center} />
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url={tileUrls[mapTile]}
        />

        {/* AOI Bounding Box */}
        <Rectangle
          bounds={bounds}
          pathOptions={{
            color: '#38BDF8',
            weight: 2,
            dashArray: '4, 4',
            fillOpacity: 0.05,
          }}
        />

        {/* Hotspot Markers */}
        {hotspots.slice(0, 100).map((h, i) => {
          const coords = h.geometry.coordinates[0][0]; // [lon, lat]
          const lat = coords[1];
          const lon = coords[0];
          const isCritical = h.properties.uhi_intensity_celsius > 4.0;

          return (
            <CircleMarker
              key={h.properties.hotspot_id || i}
              center={[lat, lon]}
              radius={isCritical ? 7 : 5}
              pathOptions={{
                color: isCritical ? '#EF4444' : '#F97316',
                fillColor: isCritical ? '#EF4444' : '#F97316',
                fillOpacity: 0.85,
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="p-1 space-y-1 font-sans text-xs">
                  <div className="font-bold text-sm text-sky-400">
                    {h.properties.hotspot_id}
                  </div>
                  <div className="flex justify-between gap-4 text-slate-200">
                    <span>Surface Temp:</span>
                    <span className="font-bold font-mono text-rose-400">
                      {h.properties.lst_celsius.toFixed(1)}°C (+{h.properties.uhi_intensity_celsius.toFixed(1)}°C)
                    </span>
                  </div>
                  <div className="flex justify-between gap-4 text-slate-300">
                    <span>Dominant Driver:</span>
                    <span className="font-semibold text-amber-300">{h.properties.dominant_driver}</span>
                  </div>
                  <div className="flex justify-between gap-4 text-slate-400">
                    <span>Albedo:</span>
                    <span>{h.properties.albedo.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between gap-4 text-slate-400">
                    <span>Vegetation (FVC):</span>
                    <span>{h.properties.fvc.toFixed(2)}</span>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

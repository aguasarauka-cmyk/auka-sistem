import React from 'react';
import { motion } from 'motion/react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { mockProspects } from '../lib/data';

// Fix for default marker icons in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom icon
const customIcon = new L.Icon({
  iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export function MapView() {
  const center = [10.4806, -66.9036]; // Caracas

  return (
    <div className="h-full flex flex-col">
      <div className="p-6 pb-4 md:p-8 md:pb-6">
        <motion.h2 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-3xl font-serif font-bold text-[#1B4332]"
        >
          Mapa Geográfico
        </motion.h2>
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-sm text-[#52796F] mt-1"
        >
          Visualización de prospectos geolocalizados
        </motion.p>
      </div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="flex-1 px-6 pb-6 md:px-8 md:pb-8"
      >
        <div className="w-full h-full rounded-3xl overflow-hidden border border-[#D8E3DB] shadow-sm relative z-0">
          <MapContainer 
            center={center as [number, number]} 
            zoom={8} 
            scrollWheelZoom={true} 
            style={{ width: '100%', height: '100%', zIndex: 0 }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
            {mockProspects.map(prospect => (
              <Marker key={prospect.id} position={[prospect.lat, prospect.lng]} icon={customIcon}>
                <Popup className="custom-popup">
                  <div className="px-1 py-0.5">
                    <h3 className="font-bold text-[#1B4332] text-sm">{prospect.empresa}</h3>
                    <p className="text-[#52796F] text-xs mt-1">{prospect.evento}</p>
                    <div className="mt-2 text-[10px] font-bold px-2 py-1 bg-[#D8F3DC] text-[#1B4332] rounded inline-block uppercase tracking-widest">
                      Score: {(prospect.score/100).toFixed(2)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </motion.div>
    </div>
  );
}

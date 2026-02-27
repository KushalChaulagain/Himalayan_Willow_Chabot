import React from "react";

// Kathmandu, near Cricket Stadium (Tribhuvan University Cricket Ground area)
const DEFAULT_LAT = 27.6751;
const DEFAULT_LON = 85.281;

interface LocationCardProps {
  mapsUrl: string;
  storeName?: string;
  address?: string;
  /** Optional: pre-built static map image URL (from backend or env) */
  staticMapUrl?: string;
  /** Optional: coordinates for Mapbox static map when VITE_MAPBOX_ACCESS_TOKEN is set */
  latitude?: number;
  longitude?: number;
}

/**
 * Builds Mapbox Static Images API URL with a custom pin.
 * Requires VITE_MAPBOX_ACCESS_TOKEN to be set.
 */
function buildMapboxStaticUrl(
  lon: number,
  lat: number,
  width: number,
  height: number
): string | null {
  const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
  if (!token) return null;
  const style = "dark-v11";
  const marker = `pin-l+ff6b00(${lon},${lat})`;
  const center = `${lon},${lat},14`;
  return `https://api.mapbox.com/styles/v1/mapbox/${style}/static/${marker}/${center}/${width}x${height}@2x?access_token=${token}`;
}

/**
 * Contextual Rich Card for store location in chat.
 * Uses a real static map when Mapbox token is available; otherwise shows an elegant fallback.
 * Rich Link layout with prominent orange CTA button.
 */
const LocationCard: React.FC<LocationCardProps> = ({
  mapsUrl,
  storeName = "Himalayan Willow",
  address = "Kathmandu, near Cricket Stadium",
  staticMapUrl: staticMapUrlProp,
  latitude = DEFAULT_LAT,
  longitude = DEFAULT_LON,
}) => {
  // 16:9 aspect ratio for map header; 400x225 at 2x = 800x450 source
  const mapWidth = 400;
  const mapHeight = 225;
  const staticMapUrl =
    staticMapUrlProp ??
    buildMapboxStaticUrl(longitude, latitude, mapWidth, mapHeight);

  return (
    <a
      href={mapsUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-2 flex flex-col rounded-xl overflow-hidden border border-zinc-800 bg-zinc-900 hover:border-zinc-700 transition-colors group max-w-[320px]"
      aria-label={`Get directions to ${storeName}`}
    >
      {/* Static Map Header - top ~60%, 16:9 */}
      <div className="relative h-32 w-full flex-shrink-0 overflow-hidden bg-zinc-800">
        {staticMapUrl ? (
          <img
            src={staticMapUrl}
            alt={`Map showing ${storeName} location`}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <>
            {/* Fallback: refined map-like placeholder (no solid blue) */}
            <div
              className="absolute inset-0"
              style={{
                background: `linear-gradient(135deg, #334155 0%, #1e293b 50%, #0f172a 100%)`,
              }}
            />
            <div
              className="absolute inset-0 opacity-30"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px)
                `,
                backgroundSize: "16px 16px",
              }}
            />
            {/* Centered pin overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div
                className="flex flex-col items-center drop-shadow-lg"
                aria-hidden
              >
                <svg
                  className="w-12 h-12 text-[#FF6B00] group-hover:scale-110 transition-transform"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                </svg>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Rich Link Content Area */}
      <div className="p-4 flex flex-col gap-2">
        <h3 className="font-bold text-white text-base leading-tight">
          {storeName}
        </h3>
        <p className="text-[13px] text-zinc-400 leading-snug">{address}</p>

        {/* Full-Width CTA Button - brand orange, thumb-friendly */}
        <div className="mt-2">
          <span className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-[#FF6B00] font-bold text-black hover:bg-[#ff8533] transition-colors group-hover:bg-[#ff8533]">
            Get Directions
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              viewBox="0 0 24 24"
              aria-hidden
            >
              {/* Navigation arrow - external link to maps */}
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
              />
            </svg>
          </span>
        </div>
      </div>
    </a>
  );
};

export default LocationCard;

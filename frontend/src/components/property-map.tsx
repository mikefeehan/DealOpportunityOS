"use client";

import "mapbox-gl/dist/mapbox-gl.css";
import type { Map as MbMap } from "mapbox-gl";
import { useEffect, useRef } from "react";
import { MAPBOX_TOKEN } from "@/lib/api";

export function PropertyMap({ lat, lon, name }: { lat: number; lon: number; name: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MbMap | null>(null);
  const hasCoords = Math.abs(lat) > 0.1 && Math.abs(lon) > 0.1;

  useEffect(() => {
    if (!MAPBOX_TOKEN || !hasCoords || !containerRef.current || mapRef.current) return;
    let cancelled = false;
    import("mapbox-gl").then(({ default: mapboxgl }) => {
      if (cancelled || !containerRef.current) return;
      mapboxgl.accessToken = MAPBOX_TOKEN;
      const map = new mapboxgl.Map({
        container: containerRef.current,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [lon, lat],
        zoom: 14
      });
      mapRef.current = map;
      map.addControl(new mapboxgl.NavigationControl(), "top-right");
      new mapboxgl.Marker({ color: "#e8c15a" })
        .setLngLat([lon, lat])
        .setPopup(
          new mapboxgl.Popup({ offset: 18 }).setHTML(
            `<div style="color:#111827;font-weight:600;font-size:13px;">${name}</div>`
          )
        )
        .addTo(map);
    });
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [lat, lon, name, hasCoords]);

  if (!MAPBOX_TOKEN) {
    return <div className="text-sm text-muted">Set NEXT_PUBLIC_MAPBOX_TOKEN to show the map.</div>;
  }
  if (!hasCoords) {
    return (
      <div className="rounded-md border border-dashed border-border bg-panel2 p-4 text-sm text-muted">
        No coordinates for this property yet — run “Geocode missing” on the Site Map.
      </div>
    );
  }
  return <div ref={containerRef} className="h-72 w-full overflow-hidden rounded-md border border-border" />;
}

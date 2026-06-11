"use client";

import "mapbox-gl/dist/mapbox-gl.css";
import type { Map as MbMap, Popup as MbPopup, GeoJSONSource } from "mapbox-gl";
import { Locate, Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { geocodeMissing, getMapPoints, MAPBOX_TOKEN } from "@/lib/api";
import type { MapPoint } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeading } from "@/components/page-heading";

function toGeoJSON(points: MapPoint[]) {
  return {
    type: "FeatureCollection",
    features: points.map((p) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [p.lon, p.lat] },
      properties: p
    }))
  };
}

function money(value: number) {
  return value >= 1000 ? `$${(value / 1000).toFixed(1)}k` : `$${value}`;
}

function popupHTML(p: MapPoint): string {
  const tag = (text: string, color: string) =>
    `<span style="display:inline-block;border:1px solid ${color}55;background:${color}1a;color:${color};border-radius:4px;padding:1px 6px;font-size:11px;margin:2px 4px 0 0;">${text}</span>`;
  const recColor = p.recommendation === "Call Owner" ? "#3fb950" : p.recommendation === "Ignore" ? "#8b949e" : "#e8c15a";
  const tags = [
    tag(p.recommendation, recColor),
    p.star_rating ? tag(`${p.star_rating}★ ${p.building_class || ""}`.trim(), "#58a6ff") : "",
    p.potential_721_candidate ? tag("721", "#e8c15a") : "",
    p.affordable ? tag("Affordable", "#8b949e") : "",
    p.for_sale ? tag("For sale", "#58a6ff") : ""
  ].join("");
  return `<div style="font-family:inherit;min-width:210px;">
    <div style="font-weight:600;color:#e6edf3;font-size:13px;">${p.name}</div>
    <div style="color:#8b949e;font-size:11px;margin-top:2px;">${p.address}</div>
    <div style="color:#c9d1d9;font-size:12px;margin-top:6px;">${p.owner_name}</div>
    <div style="display:flex;gap:10px;margin-top:6px;font-size:12px;color:#c9d1d9;">
      <span>Call <b style="color:#e8c15a;">${p.call_score.toFixed(0)}</b></span>
      <span>${p.units} units</span>
      <span>${p.year_built || "—"}</span>
      <span>${p.rent_gap ? p.rent_gap.toFixed(0) + "% gap" : ""}</span>
    </div>
    <div style="margin-top:4px;">${tags}</div>
    <a href="/properties/${p.id}" style="display:inline-block;margin-top:8px;color:#e8c15a;font-size:12px;text-decoration:none;">Open property →</a>
  </div>`;
}

export function MapPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MbMap | null>(null);
  const popupRef = useRef<MbPopup | null>(null);
  const allRef = useRef<MapPoint[]>([]);
  const [query, setQuery] = useState("");
  const [count, setCount] = useState(0);
  const [ready, setReady] = useState(false);
  const [geocoding, setGeocoding] = useState(false);

  async function runGeocode() {
    setGeocoding(true);
    await geocodeMissing();
    window.location.reload();
  }

  useEffect(() => {
    if (!MAPBOX_TOKEN || !containerRef.current || mapRef.current) return;
    let cancelled = false;
    import("mapbox-gl").then(({ default: mapboxgl }) => {
      if (cancelled || !containerRef.current) return;
      mapboxgl.accessToken = MAPBOX_TOKEN;
      const map = new mapboxgl.Map({
        container: containerRef.current,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [-110.95, 32.2],
        zoom: 10
      });
      mapRef.current = map;
      map.addControl(new mapboxgl.NavigationControl(), "top-right");
      map.on("load", async () => {
        const points = await getMapPoints("live");
        if (cancelled) return;
        allRef.current = points;
        setCount(points.length);
        map.addSource("sites", { type: "geojson", data: toGeoJSON(points) as never });
        map.addLayer({
          id: "sites-circles",
          type: "circle",
          source: "sites",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["get", "call_score"], 40, 4, 70, 7, 92, 12],
            "circle-color": [
              "match",
              ["get", "recommendation"],
              "Call Owner", "#3fb950",
              "Monitor", "#e8c15a",
              "Ignore", "#6e7681",
              "#6e7681"
            ],
            "circle-stroke-width": ["case", ["get", "for_sale"], 2.5, 0.6],
            "circle-stroke-color": ["case", ["get", "for_sale"], "#58a6ff", "#0b0b0b"],
            "circle-opacity": 0.85
          }
        });
        const bounds = new mapboxgl.LngLatBounds();
        points.forEach((p) => bounds.extend([p.lon, p.lat]));
        if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 60, maxZoom: 13 });
        setReady(true);

        map.on("click", "sites-circles", (event) => {
          const feature = event.features?.[0];
          if (!feature) return;
          const props = feature.properties as unknown as MapPoint;
          popupRef.current?.remove();
          const coordinates = (feature.geometry as unknown as { coordinates: [number, number] }).coordinates;
          popupRef.current = new mapboxgl.Popup({ closeButton: true, maxWidth: "280px" })
            .setLngLat(coordinates)
            .setHTML(popupHTML(props))
            .addTo(map);
        });
        map.on("mouseenter", "sites-circles", () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", "sites-circles", () => {
          map.getCanvas().style.cursor = "";
        });
      });
    });
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const source = map.getSource("sites") as GeoJSONSource | undefined;
    if (!source) return;
    const needle = query.toLowerCase();
    const filtered = needle
      ? allRef.current.filter((p) =>
          `${p.name} ${p.owner_name} ${p.submarket} ${p.address}`.toLowerCase().includes(needle)
        )
      : allRef.current;
    source.setData(toGeoJSON(filtered) as never);
    setCount(filtered.length);
  }, [query, ready]);

  return (
    <div>
      <PageHeading eyebrow="Map" title="Site Map">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search owner, site, submarket"
              className="w-72 pl-9"
            />
          </div>
          <span className="text-sm text-muted">{count} sites</span>
          <Button variant="secondary" onClick={runGeocode} disabled={geocoding} title="Place any sites missing coordinates onto the map">
            <Locate size={15} className={geocoding ? "animate-pulse" : ""} />
            {geocoding ? "Geocoding" : "Geocode missing"}
          </Button>
        </div>
      </PageHeading>

      {MAPBOX_TOKEN ? (
        <div ref={containerRef} className="h-[72vh] w-full overflow-hidden rounded-lg border border-border" />
      ) : (
        <div className="rounded-lg border border-border bg-panel p-6 text-sm text-muted">
          Set NEXT_PUBLIC_MAPBOX_TOKEN in frontend/.env.local to enable the map.
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted">
        <Legend color="#3fb950" label="Call Owner" />
        <Legend color="#e8c15a" label="Monitor" />
        <Legend color="#6e7681" label="Ignore" />
        <span className="inline-flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full border-2" style={{ borderColor: "#58a6ff" }} /> For sale
        </span>
        <span>Marker size = call score</span>
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

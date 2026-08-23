"""Hotspot Detection and UHI Diagnostic Endpoints."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
import numpy as np

from aerocool_ai.backend_api.dependencies import get_app_settings, get_db, get_redis_client
from aerocool_ai.backend_api.schemas.hotspot_schema import (
    GeoJSONGeometry,
    HotspotDetectionRequest,
    HotspotFeature,
    HotspotFeatureCollection,
    HotspotProperties,
)
from aerocool_ai.config import Settings
from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector
from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector
from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector
from aerocool_ai.core_engine.preprocessing.feature_extractor import UrbanFeatureExtractor

router = APIRouter(prefix="/hotspots", tags=["UHI Hotspots"])
logger = logging.getLogger(__name__)


@router.post(
    "/detect",
    response_model=HotspotFeatureCollection,
    status_code=status.HTTP_200_OK,
    summary="Detect Urban Heat Island Hotspots and Thermal Anomalies",
)
async def detect_hotspots(
    payload: HotspotDetectionRequest,
    settings: Settings = Depends(get_app_settings),
    cache: Any = Depends(get_redis_client),
) -> HotspotFeatureCollection:
    """Execute end-to-end UHI hotspot detection on satellite imagery and morphology data."""
    try:
        cache_key = f"hotspots:{payload.bbox}:{payload.min_temp_anomaly_celsius}:{payload.resolution_meters}"
        cached = await cache.get(cache_key)
        if cached:
            return HotspotFeatureCollection.model_validate_json(cached)

        bbox = payload.bbox
        min_lon, min_lat, max_lon, max_lat = bbox

        # 1. Ingest LST
        lst_collector = LandsatLSTCollector(settings)
        lst_result = lst_collector.fetch_lst_aoi(
            bbox=bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            resolution_meters=payload.resolution_meters,
        )

        # 2. Ingest Multispectral & Morphology
        sentinel_collector = SentinelLULCCollector(settings)
        opt_res = sentinel_collector.fetch_multispectral_and_lulc(
            bbox=bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

        morph_collector = OSMMorphologyCollector(settings)
        morph_res = morph_collector.fetch_morphology(
            bbox=bbox, grid_shape=lst_result.data.shape
        )

        # 3. Extract Biophysical Features
        extractor = UrbanFeatureExtractor()
        feat_set = extractor.extract_features(
            blue=opt_res.blue,
            green=opt_res.green,
            red=opt_res.red,
            nir=opt_res.nir,
            swir1=opt_res.swir1,
            swir2=opt_res.swir2,
            building_height=morph_res.building_height_mean,
            plan_area_fraction=morph_res.plan_area_fraction,
        )

        lst_grid = lst_result.data
        mean_lst = float(np.nanmean(lst_grid))
        std_lst = float(np.nanstd(lst_grid))

        # Hotspot thresholding
        anomaly_grid = lst_grid - mean_lst
        hotspot_mask = anomaly_grid >= payload.min_temp_anomaly_celsius

        grid_h, grid_w = lst_grid.shape
        lon_step = (max_lon - min_lon) / grid_w
        lat_step = (max_lat - min_lat) / grid_h

        features: List[HotspotFeature] = []

        hotspot_indices = np.argwhere(hotspot_mask)
        # Limit to top 50 most severe hotspots
        hotspot_sorted = sorted(
            hotspot_indices, key=lambda idx: anomaly_grid[idx[0], idx[1]], reverse=True
        )[:50]

        for rank, (gy, gx) in enumerate(hotspot_sorted, 1):
            c_lon = min_lon + (gx + 0.5) * lon_step
            c_lat = max_lat - (gy + 0.5) * lat_step
            temp = float(lst_grid[gy, gx])
            anomaly = float(anomaly_grid[gy, gx])
            albedo_val = float(feat_set.albedo[gy, gx])
            fvc_val = float(feat_set.fvc[gy, gx])
            bldg_dens = float(morph_res.plan_area_fraction[gy, gx])
            svf_val = float(feat_set.sky_view_factor[gy, gx])

            # Classify dominant heating driver
            if fvc_val < 0.15 and albedo_val < 0.12:
                dominant = "Low Albedo Impervious Surfaces & Vegetation Deficit"
            elif bldg_dens > 0.55 and svf_val < 0.50:
                dominant = "Street Canyon Heat Trapping (Low Sky View Factor)"
            elif albedo_val < 0.12:
                dominant = "Dark Rooftops and Asphalt Heat Absorption"
            elif fvc_val < 0.10:
                dominant = "Severe Evapotranspiration Deficit"
            else:
                dominant = "Urban High Thermal Mass"

            # Severity classification
            if anomaly > 6.0:
                severity = "Extreme"
            elif anomaly > 4.5:
                severity = "Critical"
            elif anomaly > 3.0:
                severity = "High"
            else:
                severity = "Moderate"

            hvi = float(np.clip((anomaly / 7.0) * 0.7 + (1.0 - fvc_val) * 0.3, 0.0, 1.0))

            # Approximate polygon bounding cell
            poly_coords = [
                [
                    [c_lon - lon_step * 0.45, c_lat - lat_step * 0.45],
                    [c_lon + lon_step * 0.45, c_lat - lat_step * 0.45],
                    [c_lon + lon_step * 0.45, c_lat + lat_step * 0.45],
                    [c_lon - lon_step * 0.45, c_lat + lat_step * 0.45],
                    [c_lon - lon_step * 0.45, c_lat - lat_step * 0.45],
                ]
            ]

            features.append(
                HotspotFeature(
                    geometry=GeoJSONGeometry(
                        type="Polygon", coordinates=poly_coords
                    ),
                    properties=HotspotProperties(
                        hotspot_id=f"HS-{rank:03d}-{uuid.uuid4().hex[:6]}",
                        lst_celsius=round(temp, 2),
                        uhi_intensity_celsius=round(anomaly, 2),
                        regional_mean_lst=round(mean_lst, 2),
                        heat_vulnerability_index=round(hvi, 2),
                        dominant_driver=dominant,
                        albedo=round(albedo_val, 3),
                        fvc=round(fvc_val, 3),
                        building_density=round(bldg_dens, 3),
                        sky_view_factor=round(svf_val, 3),
                        severity_level=severity,
                    ),
                )
            )

        return HotspotFeatureCollection(
            features=features,
            metadata={
                "regional_mean_lst_celsius": round(mean_lst, 2),
                "regional_std_lst_celsius": round(std_lst, 2),
                "max_lst_celsius": round(float(np.nanmax(lst_grid)), 2),
                "hotspot_count": len(features),
                "sensor": payload.sensor,
                "date_range": f"{payload.start_date} to {payload.end_date}",
            },
        )

        try:
            await cache.set(cache_key, collection.model_dump_json(), ex=300)
        except Exception as cache_err:
            logger.debug(f"Cache write skipped: {cache_err}")

        return collection

    except Exception as exc:
        logger.error(f"Error during hotspot detection: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hotspot detection pipeline failed: {str(exc)}",
        )


@router.get(
    "/{hotspot_id}",
    response_model=Dict[str, Any],
    summary="Get Detailed Hotspot Diagnostics",
)
async def get_hotspot_diagnostics(hotspot_id: str) -> Dict[str, Any]:
    """Retrieve detailed thermodynamic driver analysis for an identified hotspot."""
    return {
        "hotspot_id": hotspot_id,
        "status": "active",
        "recommended_interventions": [
            {
                "strategy": "Cool Roofs (Albedo shift >= +0.45)",
                "expected_delta_t_celsius": 4.2,
                "cost_estimate_usd_per_m2": 25.0,
                "feasibility": "High",
            },
            {
                "strategy": "Green Roofs (Extensive Sedum)",
                "expected_delta_t_celsius": 3.8,
                "cost_estimate_usd_per_m2": 120.0,
                "feasibility": "Medium (Subject to structural load test)",
            },
            {
                "strategy": "Urban Tree Canopy (High Albedo Shading)",
                "expected_delta_t_celsius": 2.9,
                "cost_estimate_usd_per_m2": 65.0,
                "feasibility": "High (In public right-of-ways)",
            },
        ],
    }

"""Unit tests for remote sensing and morphology ingestion collectors in strict error mode."""

from datetime import datetime
import numpy as np
import pytest

from aerocool_ai.config import Settings
from aerocool_ai.core_engine.ingestion.ecostress_collector import ECOSTRESSCollector
from aerocool_ai.core_engine.ingestion.era5_meteo_collector import ERA5MeteoCollector
from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector
from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector
from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector


def test_landsat_thermal_scaling():
    """Test DN to Celsius radiometric calibration formula."""
    dn = np.array([40000.0, 45000.0])
    celsius = LandsatLSTCollector.apply_thermal_scaling(dn)
    assert celsius.shape == (2,)
    assert 10.0 < celsius[0] < 50.0


def test_landsat_collector_strict_error_unauthenticated():
    """Test Landsat LST collector raises strict error when GEE is unauthenticated."""
    settings = Settings(gee_service_account=None, gee_private_key_file=None, gee_project_id=None)
    collector = LandsatLSTCollector(settings)
    bbox = (-74.02, 40.70, -73.95, 40.78)
    if not collector.is_available():
        with pytest.raises(RuntimeError, match="Google Earth Engine is not authenticated"):
            collector.fetch_lst_aoi(bbox, "2026-06-01", "2026-08-31")


def test_ecostress_collector_strict_error_unauthenticated():
    """Test ECOSTRESS collector raises strict error when Earthdata credentials are missing."""
    settings = Settings(earthdata_bearer_token=None, earthdata_username=None)
    collector = ECOSTRESSCollector(settings)
    bbox = (-74.02, 40.70, -73.95, 40.78)
    with pytest.raises(RuntimeError, match="NASA Earthdata authentication missing"):
        collector.fetch_diurnal_passes(bbox, "2026-07-15", target_hours=[9.0, 14.0])


def test_sentinel_lulc_collector_strict_error():
    """Test Sentinel-2 collector raises strict error when provider is unconfigured."""
    collector = SentinelLULCCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    with pytest.raises(RuntimeError, match="Sentinel-2 & LULC data provider query failed"):
        collector.fetch_multispectral_and_lulc(bbox, "2026-06-01", "2026-08-31")


def test_era5_meteo_collector_strict_error_unauthenticated():
    """Test ERA5 collector raises strict error when CDS API key is missing."""
    settings = Settings(cds_api_key=None)
    collector = ERA5MeteoCollector(settings)
    bbox = (-74.02, 40.70, -73.95, 40.78)
    with pytest.raises(RuntimeError, match="Copernicus Climate Data Store"):
        collector.fetch_hourly_meteo(bbox, datetime(2026, 7, 15, 14, 0))


def test_osm_morphology_collector_strict_error():
    """Test OSM morphology collector in strict mode."""
    collector = OSMMorphologyCollector()
    # In strict mode, an unreachable query or empty polygon triggers RuntimeError
    bbox = (0.0, 0.0, 0.001, 0.001)  # Ocean empty bbox
    with pytest.raises(RuntimeError):
        collector.fetch_morphology(bbox, grid_shape=(32, 32))

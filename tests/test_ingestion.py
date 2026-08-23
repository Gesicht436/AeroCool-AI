"""Unit tests for remote sensing and morphology ingestion collectors."""

from datetime import datetime
import numpy as np

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


def test_landsat_collector_fetch():
    """Test Landsat LST collector AOI querying."""
    collector = LandsatLSTCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    res = collector.fetch_lst_aoi(bbox, "2026-06-01", "2026-08-31")
    assert res.data.ndim == 2
    assert res.data.shape == (64, 64)
    assert res.crs == "EPSG:4326"
    assert not np.all(np.isnan(res.data))


def test_ecostress_collector_diurnal():
    """Test ECOSTRESS diurnal passes."""
    collector = ECOSTRESSCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    passes = collector.fetch_diurnal_passes(bbox, "2026-07-15", target_hours=[9.0, 14.0, 22.0])
    assert len(passes) == 3
    assert passes[1].local_solar_time_hours == 14.0
    # Solar noon / afternoon should be warmer than morning
    assert np.mean(passes[1].data) > np.mean(passes[0].data)


def test_sentinel_lulc_collector():
    """Test Sentinel-2 multispectral and LULC collection."""
    collector = SentinelLULCCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    res = collector.fetch_multispectral_and_lulc(bbox, "2026-06-01", "2026-08-31")
    assert res.blue.shape == (64, 64)
    assert res.nir.shape == (64, 64)
    assert res.lulc_class.shape == (64, 64)
    assert np.all(res.nir >= 0.0)


def test_era5_meteo_collector():
    """Test ERA5 atmospheric boundary conditions ingestion."""
    collector = ERA5MeteoCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    grid = collector.fetch_hourly_meteo(bbox, datetime(2026, 7, 15, 14, 0))
    assert grid.t2m_celsius.shape == (64, 64)
    assert np.all(grid.r_sw_down > 0)  # Daytime solar radiation
    assert np.all(grid.wind_speed_10m > 0)


def test_osm_morphology_collector():
    """Test 3D urban canopy morphology metrics computation."""
    collector = OSMMorphologyCollector()
    bbox = (-74.02, 40.70, -73.95, 40.78)
    morph = collector.fetch_morphology(bbox, grid_shape=(32, 32))
    assert morph.building_height_mean.shape == (32, 32)
    assert morph.plan_area_fraction.shape == (32, 32)
    assert np.all(morph.plan_area_fraction >= 0.0)
    assert np.all(morph.plan_area_fraction <= 1.0)

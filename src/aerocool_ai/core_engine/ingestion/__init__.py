"""Data ingestion submodules for satellite, meteorological, and urban morphology sources."""

from aerocool_ai.core_engine.ingestion.ecostress_collector import ECOSTRESSCollector
from aerocool_ai.core_engine.ingestion.era5_meteo_collector import ERA5MeteoCollector
from aerocool_ai.core_engine.ingestion.gee_landsat_collector import LandsatLSTCollector
from aerocool_ai.core_engine.ingestion.osm_morphology_collector import OSMMorphologyCollector
from aerocool_ai.core_engine.ingestion.sentinel_lulc_collector import SentinelLULCCollector

__all__ = [
    "LandsatLSTCollector",
    "ECOSTRESSCollector",
    "SentinelLULCCollector",
    "ERA5MeteoCollector",
    "OSMMorphologyCollector",
]

"""Unit tests for spatial preprocessing, raster normalization, and feature extraction."""

import numpy as np

from aerocool_ai.core_engine.preprocessing.feature_extractor import UrbanFeatureExtractor
from aerocool_ai.core_engine.preprocessing.raster_normalizer import RasterNormalizer
from aerocool_ai.core_engine.preprocessing.spatial_alignment import (
    AlignedGridSpecification,
    SpatialAlignmentPipeline,
)


def test_spatial_alignment_resample():
    """Test spatial resampling and multi-layer alignment."""
    pipeline = SpatialAlignmentPipeline(
        AlignedGridSpecification(bounds=(0, 0, 1, 1), target_shape=(32, 32))
    )
    arr_64 = np.random.randn(64, 64)
    arr_16 = np.random.randn(16, 16)

    aligned = pipeline.align_layers({"layer_a": arr_64, "layer_b": arr_16})
    assert aligned["layer_a"].shape == (32, 32)
    assert aligned["layer_b"].shape == (32, 32)

    stacked = pipeline.stack_feature_tensor(aligned, ["layer_a", "layer_b"])
    assert stacked.shape == (2, 32, 32)


def test_raster_normalizer_scaling_and_inpaint():
    """Test MinMax scaling and NoData inpainting."""
    normalizer = RasterNormalizer(method="minmax")
    tensor = np.array([
        [[10.0, 20.0], [30.0, 40.0]],
        [[100.0, 200.0], [300.0, 400.0]],
    ])
    normed = normalizer.fit_transform(tensor)
    assert normed.shape == (2, 2, 2)
    assert np.isclose(np.min(normed), 0.0)
    assert np.isclose(np.max(normed), 1.0)

    # Test inpainting
    gappy_raster = np.array([[10.0, np.nan], [30.0, 40.0]])
    filled = RasterNormalizer.inpaint_nodata(gappy_raster)
    assert not np.any(np.isnan(filled))


def test_urban_feature_extractor():
    """Test biophysical indicators extraction."""
    extractor = UrbanFeatureExtractor()

    red = np.full((16, 16), 0.05, dtype=np.float32)
    nir = np.full((16, 16), 0.45, dtype=np.float32)
    blue = np.full((16, 16), 0.04, dtype=np.float32)
    green = np.full((16, 16), 0.08, dtype=np.float32)
    swir1 = np.full((16, 16), 0.12, dtype=np.float32)
    swir2 = np.full((16, 16), 0.06, dtype=np.float32)
    bldg_h = np.full((16, 16), 15.0, dtype=np.float32)
    plan_area = np.full((16, 16), 0.40, dtype=np.float32)

    feat = extractor.extract_features(
        blue=blue,
        green=green,
        red=red,
        nir=nir,
        swir1=swir1,
        swir2=swir2,
        building_height=bldg_h,
        plan_area_fraction=plan_area,
    )

    assert feat.ndvi.shape == (16, 16)
    assert np.all(feat.ndvi > 0.5)  # Dense vegetation
    assert 0.0 <= np.mean(feat.albedo) <= 1.0
    assert 0.0 <= np.mean(feat.fvc) <= 1.0
    assert 0.85 <= np.mean(feat.emissivity) <= 1.0
    assert 0.0 <= np.mean(feat.sky_view_factor) <= 1.0

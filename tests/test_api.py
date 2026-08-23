"""Integration tests for FastAPI REST API endpoints."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from aerocool_ai.backend_api.dependencies import get_db
from aerocool_ai.backend_api.main import app
from aerocool_ai.database.models.scenario_results import SimulationScenario


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test /health system endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AeroCool-AI"


@pytest.mark.asyncio
async def test_hotspot_detection_endpoint():
    """Test POST /api/v1/hotspots/detect."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "bbox": [-74.02, 40.70, -73.95, 40.78],
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
            "min_temp_anomaly_celsius": 2.0,
            "resolution_meters": 30,
        }
        response = await client.post("/api/v1/hotspots/detect", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert "metadata" in data


@pytest.mark.asyncio
async def test_hotspot_diagnostics_endpoint():
    """Test GET /api/v1/hotspots/{hotspot_id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/hotspots/HS-001-a1b2c3")
        assert response.status_code == 200
        data = response.json()
        assert data["hotspot_id"] == "HS-001-a1b2c3"
        assert "recommended_interventions" in data


@pytest.mark.asyncio
async def test_optimization_allocation_endpoint():
    """Test POST /api/v1/optimization/allocate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "bbox": [-74.02, 40.70, -73.95, 40.78],
            "budget_usd": 250000.0,
            "allowed_strategies": ["cool_roof", "green_roof", "urban_canopy"],
        }
        response = await client.post("/api/v1/optimization/allocate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_spent_usd"] <= 250000.0
        assert "allocated_parcels" in data
        assert "geojson_allocation" in data


@pytest.mark.asyncio
async def test_pareto_frontier_endpoint():
    """Test POST /api/v1/optimization/pareto."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "bbox": [-74.02, 40.70, -73.95, 40.78],
            "budget_usd": 500000.0,
        }
        response = await client.post("/api/v1/optimization/pareto", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "frontier_points" in data
        assert len(data["frontier_points"]) > 0


@pytest.mark.asyncio
async def test_simulation_run_endpoint_with_mock_db():
    """Test POST /api/v1/simulation/run with mock DB session dependency."""
    mock_db = AsyncMock()
    mock_scenario = SimulationScenario(
        id="test-scenario-uuid",
        scenario_name="Test Run",
        strategy_type="green_roof",
        budget_usd=100000.0,
        status="pending",
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_scenario
    mock_db.execute.return_value = mock_result

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "scenario_name": "Test Run",
            "bbox": [-74.02, 40.70, -73.95, 40.78],
            "strategy_type": "green_roof",
            "target_area_fraction": 0.50,
            "budget_usd": 100000.0,
        }
        response = await client.post("/api/v1/simulation/run", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["scenario_name"] == "Test Run"
        assert data["mean_lst_reduction_celsius"] >= 0.0

    app.dependency_overrides.clear()

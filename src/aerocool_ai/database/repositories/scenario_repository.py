"""Simulation Scenario & Optimization Results Repository.

Provides async CRUD operations for simulation runs, impact evaluations, and scenario histories.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from geoalchemy2.functions import ST_MakeEnvelope
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aerocool_ai.database.models.scenario_results import (
    ScenarioResultRecord,
    SimulationScenario,
)

logger = logging.getLogger(__name__)


class ScenarioRepository:
    """Async repository for managing urban cooling simulation scenarios and result logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_scenario(
        self,
        scenario_name: str,
        strategy_type: str,
        budget_usd: float = 250_000.0,
        target_area_fraction: float = 0.50,
        description: Optional[str] = None,
        boundary_bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> SimulationScenario:
        """Create a new simulation scenario in pending state."""
        boundary_geom = None
        if boundary_bbox:
            minx, miny, maxx, maxy = boundary_bbox
            boundary_geom = ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)

        scenario = SimulationScenario(
            id=str(uuid.uuid4()),
            scenario_name=scenario_name,
            strategy_type=strategy_type,
            budget_usd=budget_usd,
            target_area_fraction=target_area_fraction,
            description=description,
            boundary_geom=boundary_geom,
            status="pending",
        )
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def get_scenario_by_id(
        self, scenario_id: str, load_results: bool = True
    ) -> Optional[SimulationScenario]:
        """Fetch scenario by UUID with optional eager loading of results."""
        stmt = select(SimulationScenario).where(SimulationScenario.id == scenario_id)
        if load_results:
            stmt = stmt.options(selectinload(SimulationScenario.results))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_scenarios(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SimulationScenario]:
        """List scenarios with pagination and status filter."""
        stmt = (
            select(SimulationScenario)
            .order_by(desc(SimulationScenario.created_at))
            .options(selectinload(SimulationScenario.results))
        )

        if status:
            stmt = stmt.where(SimulationScenario.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_scenario_status(
        self,
        scenario_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[SimulationScenario]:
        """Update scenario execution status."""
        scenario = await self.get_scenario_by_id(scenario_id, load_results=False)
        if not scenario:
            return None

        scenario.status = status
        scenario.error_message = error_message
        await self.session.flush()
        return scenario

    async def record_scenario_result(
        self,
        scenario_id: str,
        mean_lst_reduction: float,
        max_lst_reduction: float,
        mean_air_temp_reduction: float,
        total_area_modified_m2: float,
        total_spent_usd: float,
        annual_energy_saved_kwh: float,
        annual_co2_avoided_tons: float,
        payback_period_years: float,
        result_geojson: Dict[str, Any],
        raster_artifact_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResultRecord:
        """Persist computed thermodynamic impact results."""
        record = ScenarioResultRecord(
            scenario_id=scenario_id,
            mean_lst_reduction_celsius=mean_lst_reduction,
            max_lst_reduction_celsius=max_lst_reduction,
            mean_air_temp_reduction_celsius=mean_air_temp_reduction,
            total_area_modified_m2=total_area_modified_m2,
            total_spent_usd=total_spent_usd,
            annual_cooling_energy_saved_kwh=annual_energy_saved_kwh,
            annual_co2_avoided_tons=annual_co2_avoided_tons,
            payback_period_years=payback_period_years,
            result_geojson=result_geojson,
            raster_artifact_path=raster_artifact_path,
            metadata_json=metadata or {},
        )
        self.session.add(record)
        await self.session.flush()
        return record

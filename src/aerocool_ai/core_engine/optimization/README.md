# Urban Cooling Optimization & Spatial Allocation (`src/aerocool_ai/core_engine/optimization/`)

The `optimization` submodule translates diagnostic heat data into actionable municipal climate interventions. It simulates physical thermodynamic responses, solves constrained spatial placement problems, and computes economic and thermal comfort impacts.

---

## 🌟 Quick Primer for Juniors: What is Spatial Allocation?

If you are new to urban planning and mathematical optimization, here is the problem we solve:

### 1. The Municipal Dilemma (The Knapsack Analogy)
Imagine a city mayor gives you a fixed budget of **$250,000** (or **₹2 Crore**) to fight extreme urban heat.
- Should you paint every roof white? (Cheap, high reflection, but doesn't add moisture or shade).
- Should you build extensive green sedum roofs? (Cools via evapotranspiration, but costs 4x more per square meter).
- Should you plant urban tree canopies? (Provides critical shade and blocks sunlight, but takes space and has maintenance costs).

You cannot do everything everywhere. Every city parcel has:
- A different **baseline temperature** (some areas are blazing at $46^\circ\text{C}$, others are cooler at $36^\circ\text{C}$).
- A different **heat vulnerability index (HVI)** (areas with dense low-income elderly populations suffer far more from extreme heat than industrial zones).
- A different **cost per square meter**.

### 2. How the Spatial Allocation Solver Works
Our `SpatialAllocationSolver` models this as a **Multi-Choice Knapsack Problem** / **Mixed-Integer Linear Program (MILP)**:
$$\max \sum_{i, k} (\Delta T_{i, k} \times \text{HVI}_i \times \text{Area}_{i, k}) \cdot x_{i,k} \quad \text{subject to} \quad \sum_{i, k} c_k \cdot x_{i, k} \le \text{Budget}$$
It picks the exact combination of parcels and intervention types that yields the maximum possible temperature drop for every dollar spent.

### 3. What is the Pareto Frontier?
If you spend $50,000, you cool the worst hotspots. If you spend $250,000, you achieve significant city-wide cooling. But if you spend $2,000,000, you hit **diminishing returns** (the cooling curve flattens out).
The **Pareto Frontier** plots this tradeoff curve and automatically identifies the **"knee point"**—the mathematically recommended budget where municipal planners get the highest cooling return on their investment.

---

## Files in this Directory

### 1. [`__init__.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/__init__.py)
- **Role**: Exports public classes.
- **Exports**: `InterventionType`, `InterventionStrategy`, `CoolingInterventionSimulator`, `SpatialAllocationSolver`, `AllocationPlan`, `ImpactEvaluator`, `CoolingImpactReport`.

---

### 2. [`cooling_simulator.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/cooling_simulator.py)
- **Role**: Parametric thermodynamic simulator for urban heat mitigation strategies.
- **Key Classes & Strategies**:
  - `InterventionType` (Enum): `GREEN_ROOF`, `COOL_ROOF`, `URBAN_CANOPY`, `COOL_PAVEMENT`, `PERMEABLE_PAVEMENT`.
  - `InterventionStrategy`: Defines parameter shifts:
    - $\Delta \alpha$: Albedo increase (e.g. $+0.45$ for high-reflectance cool roofs).
    - $\Delta f_v$: Vegetation fraction increase (e.g. $+0.65$ for extensive sedum green roofs).
    - Shading factor: Solar attenuation coefficient from tree canopies.
    - Cost per $\text{m}^2$: Capital investment cost ($/m²).
  - `CoolingInterventionSimulator`:
    - Simulates spatial temperature changes:
      $$\Delta T_{\text{total}} = \frac{R_{sw} \cdot \Delta \alpha}{h_c} + \frac{\Delta f_v \cdot \lambda \text{ET}}{h_c} + \frac{\text{Shade} \cdot R_{sw}}{1.5 h_c}$$
      (where $h_c \approx 25\,\text{W}/(\text{m}^2 \text{K})$ is the convective heat transfer coefficient).
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.optimization.cooling_simulator import CoolingInterventionSimulator, InterventionType

  simulator = CoolingInterventionSimulator()
  strategy = simulator.DEFAULTS[InterventionType.COOL_ROOF]
  sim_res = simulator.simulate(base_lst, albedo_grid, fvc_grid, plan_area_grid, strategy)
  print(f"Mean cooling: {sim_res.mean_cooling_celsius:.2f} °C, Estimated cost: ${sim_res.estimated_cost_usd:,.2f}")
  ```

---

### 3. [`spatial_allocator.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/spatial_allocator.py)
- **Role**: Constrained mathematical solver finding the optimal spatial distribution of interventions under strict budget limits.
- **Key Classes & Methods**:
  - `AllocatedParcel`: Single parcel assigned an intervention, area ($\text{m}^2$), cost (\$), $\Delta T$ (°C), and priority rank.
  - `AllocationPlan`: Full municipal allocation plan, total spent, remaining budget, and categorical allocation grid.
  - `SpatialAllocationSolver`:
    - Formulates knapsack / linear relaxation and exact Mixed-Integer Linear Programming (MILP) optimization maximizing population-weighted heat relief:
      $$\max \sum_{i, k} (\Delta T_{i, k} \times \text{HVI}_i \times \text{Area}_{i, k}) \cdot x_{i,k} \quad \text{subject to} \quad \sum_{i, k} c_k \cdot x_{i, k} \le \text{Budget}, \quad \sum_k x_{i,k} \le 1, \quad x_{i,k} \in \{0, 1\}$$
    - `solve(method="greedy" | "milp")`: Solves parcel assignment via greedy heuristic or exact SciPy MILP optimizer.
    - `generate_pareto_frontier()`: Computes multi-budget Pareto efficiency curves across investment scenarios.
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.optimization.spatial_allocator import SpatialAllocationSolver

  solver = SpatialAllocationSolver()
  plan = solver.solve(
      baseline_lst=base_lst,
      albedo_grid=albedo_grid,
      fvc_grid=fvc_grid,
      plan_area_fraction=plan_area_grid,
      budget_usd=350_000.0,
      method="milp",
  )
  print(f"Allocated {len(plan.allocated_parcels)} parcels | Mean cooling: {plan.mean_cooling_celsius:.2f} °C")
  ```

---

### 4. [`impact_evaluator.py`](file:///C:/Users/mayan/Development/Projects/AeroCool-AI/src/aerocool_ai/core_engine/optimization/impact_evaluator.py)
- **Role**: Computes socioeconomic, human thermal comfort, building energy, and environmental impact metrics.
- **Key Classes & Benchmark Constants**:
  - `CoolingImpactReport`: Consolidated impact metrics.
  - `ImpactEvaluator`:
    - **Air Temperature Scaling**: $\Delta T_{\text{air}} \approx 0.35 \times \Delta T_{\text{LST}}$.
    - **Avoided HVAC Energy**: Based on ASHRAE commercial prototype benchmarks ($3.8\,\text{kWh} / (\text{m}^2 \cdot ^\circ\text{C} \cdot \text{year})$).
    - **Avoided Grid Carbon Emissions**: $0.385\,\text{kg}\,\text{CO}_2\text{e} / \text{kWh}$.
    - **Capital Payback Period**: $\text{Years} = \frac{\text{Capital Cost}}{\text{Annual Energy Cost Savings}}$.
    - **UTCI Shift**: Categorizes human physiological heat stress relief.
    - **Population Exposure Reduction**: Percentage of population removed from hazardous extreme heat zones ($> 35^\circ\text{C}$).
- **Usage Example**:
  ```python
  from aerocool_ai.core_engine.optimization.impact_evaluator import ImpactEvaluator

  evaluator = ImpactEvaluator()
  report = evaluator.evaluate(
      baseline_lst=base_lst,
      mitigated_lst=mit_lst,
      modified_area_m2=45_000.0,
      capital_investment_usd=120_000.0
  )
  print(f"Annual Energy Saved: {report.annual_cooling_energy_saved_kwh:,.0f} kWh")
  print(f"Avoided CO2: {report.annual_co2_avoided_tons:.1f} tons | Payback: {report.payback_period_years:.1f} years")
  ```

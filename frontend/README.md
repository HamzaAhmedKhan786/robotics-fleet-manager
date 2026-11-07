# FleetOS — Robotics Fleet Command Center

A futuristic, responsive control dashboard for the Robotics Fleet Manager demo.

## Stack
React 19, TypeScript, Vite 6, Lucide icons, pure CSS/SVG visualization.
Uses the existing FastAPI backend; no new database or backend dependencies.

## Run on Windows PowerShell

At your robotics-fleet-manager repository root:

```powershell
# Extract this frontend folder into .\frontend
# In terminal 1:
pixi run backend
# In terminal 2:
cd frontend
npm install
npm run dev
```

Visit http://127.0.0.1:5173

The Vite development proxy forwards `/api` and `/health` to `http://127.0.0.1:8000`.

```powershell
npm run build
```

## Features
- Fleet KPI cards, live backend health and eight-second polling
- Schematic warehouse map from `/api/v1/fleet/warehouse`
- Robot presence at stations (not real-time coordinates)
- Mission endpoint direction highlight (not a computed route)
- Robot inventory, battery/status, and activation
- Create missions, assign with Rust scheduler, start/complete/cancel
- Responsive layout, notifications, empty/error states

## Screenshot workflow
1. Seed your **development** database: `pixi run python -m scripts.seed_demo`.
2. Start both services and open http://127.0.0.1:5173.
3. Create at least one mission and assign it, then capture the overview.
4. Capture Robot fleet and Mission operations screens.
5. Save screenshots to `docs/screenshots/` in the repository and refer to them in the main README.

## Limitations
- Intended for a local demo; no authentication or public-facing security layer.
- State polling rather than streaming updates.
- Warehouse topology is fixed to the existing six demo stations.
- The moving dashed line indicates mission endpoints, not robot position or a calculated Dijkstra route.
- Robot movement is simulated by the backend when missions are completed.

import { RobotFleetView } from "./components/RobotFleetView";
import { Fragment as ReactFragment, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Activity, ArrowRight, Bot, Check, CheckCircle2,
  CircleAlert, Clock3, Command, Cpu, Database, Gauge,
  Layers3, MapPinned, Plus, Radio, RefreshCw, Route, Search,
  ShieldCheck, Signal, SquareActivity, X, Zap,
} from "lucide-react";
import { api } from "./api";
import type { FleetSummary, Mission, MissionStatus, Robot, RobotStatus, Warehouse } from "./types";
import { Warehouse3D } from "./components/Warehouse3D";

type View = "overview" | "robots" | "missions";
const ROUTES: Record<View, string> = { overview: "/overview", robots: "/robots", missions: "/missions" };
function viewFromPath(path: string): View {
  if (path === "/robots" || path.startsWith("/robots/")) return "robots";
  if (path === "/missions" || path.startsWith("/missions/")) return "missions";
  return "overview";
}
type Modal = "robot" | "mission" | null;
const POLL_INTERVAL = 2000;
const EMPTY_WAREHOUSE: Warehouse = { stations: [], edges: [] };
const STATUS_NAMES: Record<RobotStatus | MissionStatus, string> = {
  offline: "Offline", available: "Available", busy: "Busy", charging: "Charging",
  error: "Error", pending: "Pending", assigned: "Assigned", in_progress: "In progress",
  completed: "Completed", cancelled: "Cancelled", failed: "Failed",
};
const fmt = (value: string) => new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
const short = (id: string) => id.slice(0, 8).toUpperCase();
const friendlyError = (error: unknown) => error instanceof Error ? error.message : "An unexpected error occurred.";

function Status({ value }: { value: RobotStatus | MissionStatus }) {
  return <span className={`status status-${value}`}><i />{STATUS_NAMES[value]}</span>;
}

function Panel({ title, description, icon, right, children, className = "" }: {
  title: string; description?: string; icon?: ReactNode; right?: ReactNode;
  children: ReactNode; className?: string;
}) {
  return <section className={`panel ${className}`}>
    <div className="panel-head"><div className="panel-title-wrap">
      {icon && <span className="panel-head-icon">{icon}</span>}
      <div><h2>{title}</h2>{description && <p>{description}</p>}</div>
    </div>{right}</div>
    {children}
  </section>;
}

const STATION_POSITIONS: Record<string, { x: number; y: number }> = {
  "STATION-A1": { x: 130, y: 106 },
  "STATION-A2": { x: 376, y: 106 },
  "STATION-A3": { x: 622, y: 106 },
  "STATION-B1": { x: 130, y: 310 },
  "STATION-B2": { x: 376, y: 310 },
  "STATION-B3": { x: 622, y: 310 },
};

const ROUTE_COLORS = ["#44ead1", "#b4a0ff", "#ffbf76", "#72b9ff", "#ff7fbd", "#d5ef7c"];

function shortestWarehousePath(warehouse: Warehouse, start: string, end: string): string[] {
  if (!warehouse.stations.includes(start) || !warehouse.stations.includes(end)) return [];
  const costs = new Map<string, number>(warehouse.stations.map(station => [station, Infinity]));
  const previous = new Map<string, string>();
  const unvisited = new Set(warehouse.stations);
  costs.set(start, 0);
  while (unvisited.size > 0) {
    const current = [...unvisited].reduce<string | null>((best, station) =>
      best === null || (costs.get(station) ?? Infinity) < (costs.get(best) ?? Infinity) ? station : best, null);
    if (current === null || (costs.get(current) ?? Infinity) === Infinity) break;
    if (current === end) break;
    unvisited.delete(current);
    for (const edge of warehouse.edges) {
      const neighbor = edge.source === current ? edge.target : edge.target === current ? edge.source : null;
      if (neighbor === null || !unvisited.has(neighbor)) continue;
      const candidate = (costs.get(current) ?? Infinity) + edge.distance;
      if (candidate < (costs.get(neighbor) ?? Infinity)) {
        costs.set(neighbor, candidate);
        previous.set(neighbor, current);
      }
    }
  }
  if (start === end) return [start];
  if (!previous.has(end)) return [];
  const route = [end];
  while (route[0] !== start) {
    const parent = previous.get(route[0]);
    if (!parent) return [];
    route.unshift(parent);
  }
  return route;
}

function WarehouseMap({ warehouse, robots, missions, selectedMission, onSelectMission }: {
  warehouse: Warehouse; robots: Robot[]; missions: Mission[];
  selectedMission: string | null; onSelectMission: (id: string | null) => void;
}) {
  const active = useMemo(
    () => missions.filter(m => m.status === "assigned" || m.status === "in_progress")
      .sort((a, b) => a.created_at.localeCompare(b.created_at)),
    [missions],
  );
  const [showAll, setShowAll] = useState(true);
  const routes = useMemo(() => active.map((mission, index) => ({
    mission,
    color: ROUTE_COLORS[index % ROUTE_COLORS.length],
    stations: mission.plan?.path?.length
      ? mission.plan.path
      : shortestWarehousePath(
          warehouse,
          mission.pickup_location,
          mission.delivery_location,
        ),
    robot: robots.find(robot => robot.id === mission.assigned_robot_id),
  })), [active, robots, warehouse]);
  const selectedRoute = routes.find(route => route.mission.id === selectedMission) ?? routes[0];
  const visibleRoutes = showAll ? routes : selectedRoute ? [selectedRoute] : [];
  const unknownStations = warehouse.stations.filter(station => !STATION_POSITIONS[station]);
  return <Panel title="Warehouse network" description="Topology-based route overview · simulated operations"
    icon={<MapPinned size={17} />} className="warehouse-panel"
    right={<span className="panel-meta"><span className="live-dot" />{warehouse.stations.length} stations · {active.length} active routes</span>}>
    <div className="map-topbar">
      <span><span className="legend-dot available" />Available robot</span>
      <span><span className="legend-dot busy" />Busy robot</span>
      <span><span className="legend-dot charging" />Charging robot</span>
      <span><span className="legend-line" />Graph-based route</span>
      <label className="routes-switch"><input type="checkbox" checked={showAll} onChange={event => setShowAll(event.target.checked)} /> Show all routes</label>
    </div>
    <div className="warehouse-canvas">
      {warehouse.stations.length === 0 ? <div className="map-empty">Warehouse data unavailable</div> :
        <svg viewBox="0 0 752 416" role="img" aria-label={`Warehouse network with ${active.length} active mission routes`}>
          <defs>
            <pattern id="warehouseDots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#375271" opacity=".43" /></pattern>
            <filter id="routeGlow"><feGaussianBlur stdDeviation="2.5" result="soft" /><feMerge><feMergeNode in="soft" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <rect width="752" height="416" fill="url(#warehouseDots)" />
          <text x="24" y="30" className="map-caption">SECTOR A / NORTH AISLE</text>
          <text x="24" y="396" className="map-caption">SECTOR B / SOUTH AISLE</text>
          {warehouse.edges.map(edge => {
            const from = STATION_POSITIONS[edge.source];
            const to = STATION_POSITIONS[edge.target];
            if (!from || !to) return null;
            return <g key={`${edge.source}-${edge.target}`}>
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#243c53" strokeWidth="19" strokeLinecap="round" />
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#496480" strokeWidth="1.5" strokeDasharray="4 9" />
              <title>{edge.source} ↔ {edge.target} · distance {edge.distance}</title>
            </g>;
          })}
          {visibleRoutes.map(route => {
            const focused = selectedRoute?.mission.id === route.mission.id;
            const routeIndex = routes.findIndex(item => item.mission.id === route.mission.id);
            const offset = (routeIndex % 5 - 2) * 4;
            const positions = route.stations.map(station => STATION_POSITIONS[station]).filter(Boolean);
            const coordinateList = positions.map(position => `${position.x + offset},${position.y + offset}`).join(" ");
            const start = positions[0];
            const end = positions[positions.length - 1];
            if (!start || !end) return null;
            return <g key={route.mission.id} opacity={focused ? 1 : 0.72}>
              <polyline points={coordinateList} fill="none" stroke="#070f1e" strokeWidth={focused ? 10 : 8} strokeLinejoin="round" strokeLinecap="round" />
              <polyline points={coordinateList} fill="none" stroke={route.color} strokeWidth={focused ? 4.5 : 3}
                strokeDasharray="11 8" strokeLinejoin="round" strokeLinecap="round" filter={focused ? "url(#routeGlow)" : undefined}
                className="mission-line" />
              {route.stations.length > 1 && <circle cx={end.x + offset} cy={end.y + offset} r="7" fill={route.color} stroke="#0b1829" strokeWidth="2" />}
              {route.stations.length === 1 && <circle cx={start.x + offset} cy={start.y + offset} r="29" stroke={route.color} strokeWidth="3" fill="none" strokeDasharray="6 5" />}
              <title>Mission {short(route.mission.id)} · {route.robot?.name ?? "Unassigned"} · {route.stations.join(" → ")}</title>
            </g>;
          })}
          {warehouse.stations.map(station => {
            const pos = STATION_POSITIONS[station];
            if (!pos) return null;
            const local = robots.filter(robot => robot.current_location === station);
            const selectedHere = selectedRoute && (
              selectedRoute.mission.pickup_location === station || selectedRoute.mission.delivery_location === station
            );
            return <g key={station}>
              {selectedHere && <rect x={pos.x - 57} y={pos.y - 32} width="114" height="64" rx="15" fill="none" stroke={selectedRoute.color} strokeWidth="1.8" strokeDasharray="5 5" opacity=".9" />}
              <rect x={pos.x - 49} y={pos.y - 24} width="98" height="48" rx="12" fill="#101f33" stroke="#496682" strokeWidth="1.5" />
              <circle cx={pos.x - 29} cy={pos.y} r="4" fill={local.some(robot => robot.status === "busy") ? "#b4a0ff" : local.some(robot => robot.status === "charging") ? "#ffc36b" : local.some(robot => robot.status === "available") ? "#3ce5cf" : "#536881"} />
              <text x={pos.x + 7} y={pos.y + 5} className="station-label" textAnchor="middle">{station.replace("STATION-", "")}</text>
              {local.length > 0 && <g>
                <rect x={pos.x - 37} y={pos.y + 34} width="74" height="22" rx="11" fill="#162c3e" stroke="#3d6675" />
                <text x={pos.x} y={pos.y + 49} className="robot-count" textAnchor="middle">{local.length} ROBOT{local.length > 1 ? "S" : ""}</text>
              </g>}
              <title>{station}: {local.length ? local.map(robot => `${robot.name} (${robot.status})`).join(", ") : "No robots"}</title>
            </g>;
          })}
        </svg>}
    </div>
    {unknownStations.length > 0 && <p className="muted tiny">Stations without layout coordinates: {unknownStations.join(", ")}</p>}
    <div className="route-list-heading">
      <div><strong>ACTIVE MISSION ROUTES</strong><p>Each mission is shown separately. Select a route to highlight it.</p></div>
      <span className="route-count">{routes.length} route{routes.length !== 1 ? "s" : ""}</span>
    </div>
    <div className="route-list">
      {routes.length === 0 && <div className="route-empty">No active mission routes. Assign a pending mission to display its path.</div>}
      {routes.map(route => <button type="button" key={route.mission.id}
        className={`route-item ${selectedRoute?.mission.id === route.mission.id ? "selected" : ""}`}
        onClick={() => onSelectMission(route.mission.id)}>
        <span className="route-color" style={{ background: route.color }} />
        <span className="route-details"><strong>#{short(route.mission.id)} <span>· {route.robot?.name ?? "Unknown robot"}</span></strong>
          <small>{route.mission.pickup_location.replace("STATION-", "")} → {route.mission.delivery_location.replace("STATION-", "")} · {route.stations.length ? route.stations.map(s => s.replace("STATION-", "")).join(" → ") : "No connected path"}</small></span>
        <Status value={route.mission.status} />
      </button>)}
    </div>
    <p className="map-disclaimer">Routes are shortest paths calculated in the browser from the warehouse graph, not robot telemetry or confirmed travel progress. Markers show last known station and status.</p>
  </Panel>;
}

function Metric({ icon, title, value, detail, accent }: {
  icon: ReactNode; title: string; value: number; detail: string; accent: string;
}) {
  return <div className="metric"><div className="metric-top"><span>{title}</span><span className={`metric-icon ${accent}`}>{icon}</span></div>
    <div className="metric-value">{value.toString().padStart(2, "0")}</div><p>{detail}</p></div>;
}

function BatteryLevel({ value }: { value: number }) {
  const tone = value < 30 ? "low" : value < 60 ? "medium" : "high";
  return <div className="battery"><div className="battery-track"><div className={`battery-fill ${tone}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></div><span>{Math.round(value)}%</span></div>;
}

function RobotsTable({ robots, busy, onActivate }: { robots: Robot[]; busy: string | null; onActivate: (robot: Robot) => void }) {
  return <div className="table-wrap"><table><thead><tr><th>Robot</th><th>State</th><th>Battery</th><th>Station</th><th>Action</th></tr></thead><tbody>
    {robots.map(robot => <tr key={robot.id}><td><div className="robot-identity"><span className="robot-avatar"><Bot size={18} /></span><span><strong>{robot.name}</strong><small>#{short(robot.id)}</small></span></div></td>
      <td><Status value={robot.status} /></td><td><BatteryLevel value={robot.battery_level} /></td>
      <td><span className="station-text">{robot.current_location || "Not set"}</span></td><td>
        {robot.status === "offline" && robot.current_location && robot.battery_level >= 30 ? <button className="small-action" disabled={busy !== null} onClick={() => onActivate(robot)}>Activate</button> : <span className="muted">—</span>}
      </td></tr>)}
    {robots.length === 0 && <tr><td colSpan={5} className="empty-row">No robots registered. Select “Add robot” to create one.</td></tr>}
  </tbody></table></div>;
}


function MissionsTable({
  missions,
  robots,
  busy,
  onAction,
}: {
  missions: Mission[];
  robots: Robot[];
  busy: string | null;
  onAction: (
    mission: Mission,
    action: "assign" | "start" | "complete" | "cancel",
  ) => void;
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const sorted = [...missions].sort(
    (a, b) => b.created_at.localeCompare(a.created_at),
  );

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Mission</th>
            <th>Route</th>
            <th>Robot</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Details</th>
          </tr>
        </thead>

        <tbody>
          {sorted.map((mission) => {
            const robot = robots.find(
              r => r.id === mission.assigned_robot_id,
            );

            const expanded = expandedId === mission.id;
            const plan = mission.plan;

            return (
              <ReactFragment key={mission.id}>
                <tr>
                  <td>
                    <strong className="mono">
                      #{short(mission.id)}
                    </strong>
                    <small className="cell-sub">
                      {fmt(mission.created_at)}
                    </small>
                  </td>

                  <td>
                    <div className="route-cell">
                      <strong>
                        {mission.pickup_location.replace("STATION-", "")}
                      </strong>
                      <ArrowRight size={13} />
                      <strong>
                        {mission.delivery_location.replace("STATION-", "")}
                      </strong>
                    </div>
                  </td>

                  <td>
                    {robot?.name ?? (
                      <span className="muted">
                        {mission.assigned_robot_id
                          ? `#${short(mission.assigned_robot_id)}`
                          : "Awaiting dispatch"}
                      </span>
                    )}
                  </td>

                  <td>
                    <span className="priority">
                      P{mission.priority}
                    </span>
                  </td>

                  <td>
                    <Status value={mission.status} />
                  </td>

                  <td>
                    <div className="action-group">
                      <button
                        className="small-action"
                        onClick={() =>
                          setExpandedId(expanded ? null : mission.id)
                        }
                      >
                        {expanded ? "Hide" : "Why / Route"}
                      </button>

                      {(mission.status === "pending" ||
                        mission.status === "assigned") && (
                        <button
                          className="icon-button subtle"
                          disabled={busy !== null}
                          title="Cancel mission before movement"
                          onClick={() => onAction(mission, "cancel")}
                        >
                          <X size={15} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>

                {expanded && (
                  <tr className="mission-details-row">
                    <td colSpan={6}>
                      <div className="mission-explanation">
                        <div>
                          <span className="explain-label">
                            SCHEDULER DECISION
                          </span>
                          <p>
                            {mission.selection_reason ??
                              "Waiting for an eligible robot. " +
                              "The autonomous dispatcher will retry."}
                          </p>
                        </div>

                        {plan && (
                          <>
                            <div className="explain-stats">
                              <div>
                                <small>Route distance</small>
                                <strong>
                                  {plan.total_distance.toFixed(1)}
                                </strong>
                              </div>

                              <div>
                                <small>Energy estimate</small>
                                <strong>
                                  {plan.energy_required.toFixed(2)}%
                                </strong>
                              </div>

                              <div>
                                <small>Battery after</small>
                                <strong>
                                  {plan.battery_after.toFixed(1)}%
                                </strong>
                              </div>

                              <div>
                                <small>Simulated duration</small>
                                <strong>
                                  {plan.duration_seconds}s
                                </strong>
                              </div>
                            </div>

                            <div className="mission-path">
                              <span className="explain-label">
                                PLANNED STATION PATH
                              </span>
                              <p>
                                {plan.path.join(" → ")}
                              </p>
                            </div>
                          </>
                        )}

                        {mission.finished_at && (
                          <p className="completion-time">
                            Completed: {fmt(mission.finished_at)}
                          </p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </ReactFragment>
            );
          })}

          {sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="empty-row">
                No missions created yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function NewMission({ stations, onClose, onSubmit, saving }: {
  stations: string[]; onClose: () => void;
  onSubmit: (payload: { pickup_location: string; delivery_location: string; priority: number }) => Promise<void>;
  saving: boolean;
}) {
  const [pickup, setPickup] = useState(stations[0] || "");
  const [delivery, setDelivery] = useState(stations[stations.length - 1] || "");
  const [priority, setPriority] = useState(3);
  const valid = pickup && delivery && pickup !== delivery;
  return <form onSubmit={event => { event.preventDefault(); if (valid) void onSubmit({ pickup_location: pickup, delivery_location: delivery, priority }); }}>
    <label>Pickup station<select value={pickup} onChange={event => setPickup(event.target.value)} required>{stations.map(s => <option key={s}>{s}</option>)}</select></label>
    <label>Delivery station<select value={delivery} onChange={event => setDelivery(event.target.value)} required>{stations.map(s => <option key={s}>{s}</option>)}</select></label>
    <label>Priority <span className="label-hint">1 = lowest · 5 = highest</span>
      <input type="range" min="1" max="5" value={priority} onChange={event => setPriority(Number(event.target.value))} /><span className="range-number">Priority {priority}</span></label>
    {!valid && <p className="form-error">Pickup and delivery must be different stations.</p>}
    <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button type="submit" className="button primary" disabled={!valid || saving}>{saving ? "Creating..." : "Create mission"}</button></div>
  </form>;
}

function NewRobot({ stations, onClose, onSubmit, saving }: {
  stations: string[]; onClose: () => void;
  onSubmit: (payload: { name: string; battery_level: number; current_location: string }) => Promise<void>;
  saving: boolean;
}) {
  const [name, setName] = useState(""); const [station, setStation] = useState(stations[0] || ""); const [battery, setBattery] = useState(100);
  return <form onSubmit={event => { event.preventDefault(); void onSubmit({ name: name.trim(), battery_level: battery, current_location: station }); }}>
    <label>Robot name<input required minLength={1} maxLength={100} value={name} onChange={event => setName(event.target.value)} placeholder="AMR-005" /></label>
    <label>Initial station<select value={station} onChange={event => setStation(event.target.value)} required>{stations.map(s => <option key={s}>{s}</option>)}</select></label>
    <label>Battery level <span className="label-hint">0–100%</span><input type="range" min="0" max="100" value={battery} onChange={event => setBattery(Number(event.target.value))} /><span className="range-number">{battery}%</span></label>
    <p className="form-note">New robots start offline. Activate them from the robot table after registration.</p>
    <div className="modal-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button type="submit" className="button primary" disabled={!name.trim() || !station || saving}>{saving ? "Adding..." : "Register robot"}</button></div>
  </form>;
}

export default function App() {
  const [view, setView] = useState<View>(() => viewFromPath(window.location.pathname));
  const [warehouseMode, setWarehouseMode] = useState<"2d" | "3d">("3d");
  const navigate = useCallback((next: View) => {
    if (window.location.pathname !== ROUTES[next]) window.history.pushState({}, "", ROUTES[next]);
    setView(next);
    setSearch("");
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);
  useEffect(() => {
    if (window.location.pathname === "/") window.history.replaceState({}, "", "/overview");
    const handlePopState = () => { setView(viewFromPath(window.location.pathname)); setSearch(""); };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);
  const [robots, setRobots] = useState<Robot[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [warehouse, setWarehouse] = useState<Warehouse>(EMPTY_WAREHOUSE);
  const [online, setOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ message: string; error: boolean } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [modal, setModal] = useState<Modal>(null);
  const [selectedMission, setSelectedMission] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const previousMissionStates = useRef(
    new Map<string, MissionStatus>(),
  );
  const initialSync = useRef(false);

  const refresh = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [health, s, w, r, m] = await Promise.all([
        api.health(), api.summary(), api.warehouse(), api.robots(), api.missions(),
      ]);
      setOnline(health.status === "healthy"); setSummary(s); setWarehouse(w);
      setRobots(r);
      setMissions(m);
      setError(null);
      setLastUpdated(new Date());

      if (initialSync.current) {
        const newlyCompleted = m.filter(
          mission =>
            mission.status === "completed" &&
            previousMissionStates.current.has(mission.id) &&
            previousMissionStates.current.get(mission.id) !== "completed"
        );

        if (newlyCompleted.length > 0) {
          const mission = newlyCompleted[0];

          setNotice({
            message:
              `Mission #${short(mission.id)} completed automatically. ` +
              `Robot returned to available or charging state.`,
            error: false,
          });
        }
      }

      previousMissionStates.current = new Map(
        m.map(mission => [mission.id, mission.status]),
      );

      initialSync.current = true;
    } catch (e) {
      setOnline(false); setError(friendlyError(e));
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); const timer = window.setInterval(() => { if (document.visibilityState === "visible" && !busy) void refresh(true); }, POLL_INTERVAL); return () => window.clearInterval(timer); }, [refresh, busy]);

  const run = async (key: string, work: () => Promise<unknown>, success: string) => {
    setBusy(key); setNotice(null);
    try { await work(); setNotice({ message: success, error: false }); setModal(null); await refresh(true); }
    catch (e) { setNotice({ message: friendlyError(e), error: true }); }
    finally { setBusy(null); }
  };
  
  const filteredMissions = useMemo(() => missions.filter(m => `${m.id} ${m.pickup_location} ${m.delivery_location} ${m.status}`.toLowerCase().includes(search.toLowerCase())), [missions, search]);
  const latestMissions = useMemo(() => [...missions].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 6), [missions]);

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-icon"><Command size={24} /></div><div><strong>FLEET<span>OS</span></strong><small>COMMAND CENTER</small></div></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav aria-label="Main navigation"><a href="/overview" aria-current={view === "overview" ? "page" : undefined} className={view === "overview" ? "nav-link active" : "nav-link"} onClick={event => { if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); navigate("overview"); } }}><Gauge size={18} /> Overview</a>
        <a href="/robots" aria-current={view === "robots" ? "page" : undefined} className={view === "robots" ? "nav-link active" : "nav-link"} onClick={event => { if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); navigate("robots"); } }}><Bot size={18} /> Robot fleet <span className="nav-counter">{robots.length}</span></a>
        <a href="/missions" aria-current={view === "missions" ? "page" : undefined} className={view === "missions" ? "nav-link active" : "nav-link"} onClick={event => { if (!event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey && event.button === 0) { event.preventDefault(); navigate("missions"); } }}><Route size={18} /> Missions <span className="nav-counter">{missions.filter(m => m.status === "pending" || m.status === "assigned" || m.status === "in_progress").length}</span></a>
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-system"><span className="sidebar-label">SYSTEM STACK</span><div><Cpu size={16} /><span>Rust scheduler</span><Check size={14} className="green" /></div><div><Database size={16} /><span>PostgreSQL</span><Check size={14} className="green" /></div><div><Layers3 size={16} /><span>FastAPI</span><Check size={14} className="green" /></div></div>
      <div className="sidebar-bottom"><ShieldCheck size={17} /><div><strong>LOCAL DEMO</strong><small>Simulated mission controls</small></div></div>
    </aside>

    <main className="main"><header className="topbar"><div className="breadcrumbs">WORKSPACE <span>/</span> <strong>{view === "overview" ? "OVERVIEW" : view.toUpperCase()}</strong></div>
      <div className="topbar-right"><span className="header-clock"><Clock3 size={14} /> {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Not synced"}</span>
        <span className={`connection ${online ? "connected" : "disconnected"}`}><span className="live-dot" />{online ? "API ONLINE" : "API OFFLINE"}</span>
        <button className="icon-button" onClick={() => void refresh()} aria-label="Refresh dashboard" title="Refresh"><RefreshCw size={18} className={loading ? "spinning" : ""} /></button></div></header>

      <div className="page-body"><div className="hero"><div><div className="eyebrow"><Radio size={14} /> FLEET OPERATIONS / LIVE OVERVIEW</div><h1>{view === "overview" ? "Mission Control" : view === "robots" ? "Robot Fleet" : "Mission Operations"}<span className="heading-dot">.</span></h1><p>{view === "overview" ? "A unified view of autonomous fleet coordination and warehouse operations." : view === "robots" ? "Manage robot readiness, telemetry, and station assignments." : "Dispatch and supervise simulated warehouse delivery missions."}</p></div>
        <div className="hero-actions"><button className="button secondary" onClick={() => void refresh()}><RefreshCw size={16} /> Refresh</button>
          {view === "overview" && (
            <button
              className="button demo-button"
              disabled={busy !== null || !online}
              onClick={() =>
                void run(
                  "demo",
                  () => api.demoSimulation(),
                  "Two demo missions queued. Existing eligible robots are assigned automatically.",
                )
              }
            >
              <Zap size={17} />
              {busy === "demo" ? "Preparing demo..." : "Run Autonomous Demo"}
            </button>
          )}
          <button className="button primary" onClick={() => setModal(view === "robots" ? "robot" : "mission")}><Plus size={17} /> {view === "robots" ? "Add robot" : "New mission"}</button></div></div>

        {error && <div className="error-banner"><CircleAlert size={18} /><div><strong>Backend connection problem</strong><p>{error}</p></div><button onClick={() => void refresh()}>Retry</button></div>}
        {notice && <div className={`notice ${notice.error ? "notice-error" : "notice-success"}`}><span>{notice.error ? <CircleAlert size={17} /> : <CheckCircle2 size={17} />}</span>{notice.message}<button className="icon-button" onClick={() => setNotice(null)} aria-label="Dismiss message"><X size={15} /></button></div>}

        <div className="metrics-grid">
          <Metric title="TOTAL ROBOTS" value={summary?.total_robots ?? 0} detail="Registered fleet units" icon={<Bot size={20} />} accent="cyan" />
          <Metric title="AVAILABLE" value={summary?.available_robots ?? 0} detail="Ready for new missions" icon={<Signal size={20} />} accent="green" />
          <Metric title="ACTIVE MISSIONS" value={summary?.active_missions ?? 0} detail="Assigned or in progress" icon={<Zap size={20} />} accent="purple" />
          <Metric title="COMPLETED" value={summary?.completed_missions ?? 0} detail="Successfully delivered" icon={<CheckCircle2 size={20} />} accent="gold" />
        </div>

        {view === "overview" && <>
          <div className="overview-grid"><div>
            <div className="warehouse-mode-switch">
              <button
                type="button"
                className={warehouseMode === "3d" ? "active" : ""}
                onClick={() => setWarehouseMode("3d")}
              >
                3D Warehouse
              </button>

              <button
                type="button"
                className={warehouseMode === "2d" ? "active" : ""}
                onClick={() => setWarehouseMode("2d")}
              >
                2D Network
              </button>
            </div>

            {warehouseMode === "3d" ? (
              <Warehouse3D
                warehouse={warehouse}
                robots={robots}
                missions={missions}
              />
            ) : (
              <WarehouseMap
                warehouse={warehouse}
                robots={robots}
                missions={missions}
                selectedMission={selectedMission}
                onSelectMission={setSelectedMission}
              />
            )}
          </div>
            <Panel title="Fleet health" description="Current robot operating states" icon={<Activity size={17} />} className="health-panel" right={<span className="panel-meta">LIVE DATA</span>}>
              <div className="fleet-donut" style={{ background: `conic-gradient(#3ce5cf 0 ${robots.length ? 100 * (summary?.available_robots ?? 0) / robots.length : 0}%, #a095ff 0 ${robots.length ? 100 * ((summary?.available_robots ?? 0) + (summary?.active_robots ?? 0)) / robots.length : 0}%, #ffc46e 0 ${robots.length ? 100 * ((summary?.available_robots ?? 0) + (summary?.active_robots ?? 0) + (summary?.charging_robots ?? 0)) / robots.length : 0}%, #45546b 0 100%)` }}><div><strong>{robots.length}</strong><span>ROBOTS</span></div></div>
              <div className="health-rows">{(["available", "busy", "charging", "offline", "error"] as const).map(state => <div key={state}><span><i className={`legend-dot ${state}`} />{STATUS_NAMES[state]}</span><strong>{summary?.robots_by_status?.[state] ?? 0}</strong></div>)}</div>
              <div className="system-note"><SquareActivity size={16} /><div><strong>Automated fleet coordination</strong><p>Rust selects eligible robots using warehouse distance and battery constraints.</p></div></div>
            </Panel></div>
          <div className="bottom-grid"><Panel title="Robot inventory" description="Fleet telemetry and readiness" icon={<Bot size={17} />} right={<button className="text-link" onClick={() => navigate("robots")}>View all <ArrowRight size={15} /></button>}>
            <RobotsTable robots={robots.slice(0, 5)} busy={busy} onActivate={robot => void run(robot.id, () => api.updateRobot(robot.id, { status: "available" }), `${robot.name} is now available.`)} />
          </Panel>
          <Panel title="Recent missions" description="Latest warehouse orders" icon={<Route size={17} />} right={<button className="text-link" onClick={() => navigate("missions")}>View all <ArrowRight size={15} /></button>}>
            <div className="recent-list">{latestMissions.map(m => <div className="recent-mission" key={m.id}><span className="mission-symbol"><Route size={17} /></span><div><strong>#{short(m.id)}</strong><small>{m.pickup_location.replace("STATION-", "")} <ArrowRight size={11} /> {m.delivery_location.replace("STATION-", "")}</small></div><Status value={m.status} /></div>)}
            {!latestMissions.length && <div className="empty-inline">No missions yet.</div>}</div>
          </Panel></div>
        </>}

        
        {view === "robots" && (
          <RobotFleetView
            robots={robots}
            missions={missions}
            busy={busy}
            onUpdate={(robot, changes) => {
              void run(
                robot.id,
                () => api.updateRobot(robot.id, changes),
                `${robot.name} operating state updated successfully.`,
              );
            }}
          />
        )}


        {view === "missions" && <Panel title="Mission queue" description="Autonomous dispatch, route planning, energy-aware scheduling and mission history" icon={<Route size={17} />} right={<span className="panel-meta">{filteredMissions.length} MISSIONS</span>}>
          <div className="table-toolbar"><div className="search-wrap"><Search size={16} /><input aria-label="Search missions" placeholder="Search mission, station or status" value={search} onChange={e => setSearch(e.target.value)} /></div><button className="button secondary" onClick={() => setModal("mission")}><Plus size={16} /> New mission</button></div>
          <MissionsTable missions={filteredMissions} robots={robots} busy={busy} onAction={(mission, action) => void run(mission.id, () => api.missionAction(mission.id, action), `Mission #${short(mission.id)} ${action === "assign" ? "assigned" : action === "start" ? "started" : action === "complete" ? "completed" : "cancelled"}.`)} />
        </Panel>}
        <footer className="footer"><span><span className="footer-mark">◆</span> FLEETOS / ROBOTICS CONTROL CENTER</span><span>DEMO ENVIRONMENT <span className="footer-separator">·</span> 2s POLLING <span className="footer-separator">·</span> PYTHON + RUST + POSTGRESQL</span></footer>
      </div>
    </main>

    {modal && <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) setModal(null); }}><div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-header"><div><div className="eyebrow">FLEET OPERATIONS</div><h2 id="modal-title">{modal === "robot" ? "Register a robot" : "Create a mission"}</h2></div><button className="icon-button" onClick={() => setModal(null)} aria-label="Close dialog"><X size={18} /></button></div>
      {modal === "mission" ? <NewMission stations={warehouse.stations} onClose={() => setModal(null)} saving={busy !== null} onSubmit={payload => run("create", () => api.createMission(payload), "Mission queued. Autonomous dispatch will select an eligible robot.")} /> : <NewRobot stations={warehouse.stations} onClose={() => setModal(null)} saving={busy !== null} onSubmit={payload => run("create", () => api.createRobot(payload), "Robot registered in offline mode.")} />}
    </div></div>}
  </div>;
}

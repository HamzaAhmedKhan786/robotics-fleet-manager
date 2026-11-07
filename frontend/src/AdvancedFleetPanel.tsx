import { useEffect, useState } from "react";

type RobotSnapshot = {
  id: string;
  name: string;
  status: string;
  position_x: number | null;
  position_z: number | null;
  movement_progress: number;
};
type Mission = { id: string; status: string; assigned_robot_id: string | null; pickup_location: string; delivery_location: string; plan: { paused?: boolean; traffic_state?: string } | null };
type HistoryPoint = { id: number; position_x: number; position_z: number; velocity: number; progress: number; recorded_at: string };
type SnapshotEvent = { type: string; robots: RobotSnapshot[] };

export function AdvancedFleetPanel() {
  const [token, setToken] = useState(() => sessionStorage.getItem("fleetos_access_token") || "");
  const [connected, setConnected] = useState(false);
  const [robots, setRobots] = useState<RobotSnapshot[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [robotId, setRobotId] = useState("");
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [replayIndex, setReplayIndex] = useState(0);
  const [error, setError] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    const onAuth = () => setToken(sessionStorage.getItem("fleetos_access_token") || "");
    window.addEventListener("fleetos-auth-changed", onAuth);
    return () => window.removeEventListener("fleetos-auth-changed", onAuth);
  }, []);

  useEffect(() => {
    if (!token) { setRobots([]); setMissions([]); return; }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/api/v1/operations/ws/telemetry`);
    socket.onopen = () => socket.send(JSON.stringify({ token }));
    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as SnapshotEvent;
        if (payload.type === "fleet.snapshot") {
          setRobots(payload.robots);
          setConnected(true);
        }
      } catch { setError("Invalid telemetry message"); }
    };
    socket.onerror = () => setError("Live telemetry connection unavailable");
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let active = true;
    async function refresh() {
      try {
        const response = await fetch("/api/v1/missions", { headers: { Authorization: `Bearer ${token}` } });
        if (!response.ok) throw new Error(`Mission API returned ${response.status}`);
        const data = await response.json() as Mission[];
        if (active) setMissions(data);
      } catch (e) { if (active) setError(e instanceof Error ? e.message : "Mission request failed"); }
    }
    void refresh();
    const handle = window.setInterval(() => { void refresh(); }, 3000);
    return () => { active = false; window.clearInterval(handle); };
  }, [token]);

  async function replayHistory(id: string) {
    setRobotId(id);
    if (!token || !id) return;
    try {
      const response = await fetch(`/api/v1/operations/robots/${id}/history?limit=500`, { headers });
      if (!response.ok) throw new Error(`History API returned ${response.status}`);
      const points = await response.json() as HistoryPoint[];
      setHistory(points);
      setReplayIndex(Math.max(0, points.length - 1));
    } catch (e) { setError(e instanceof Error ? e.message : "History unavailable"); }
  }

  async function operate(id: string, action: "pause" | "resume" | "restart") {
    try {
      const response = await fetch(`/api/v1/operations/missions/${id}/${action}`, {
        method: "POST", headers,
      });
      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        const detail = (payload && typeof payload === "object" && "detail" in payload)
          ? String((payload as { detail: unknown }).detail) : `HTTP ${response.status}`;
        throw new Error(detail);
      }
      setError(`Mission ${id.slice(0, 8)}: ${action} acknowledged`);
    } catch (e) { setError(e instanceof Error ? e.message : "Mission control failed"); }
  }

  const selected = history[replayIndex];
  return <section aria-label="Advanced fleet telemetry" style={{ padding: 16 }}>
    <h3>Advanced Fleet Operations</h3>
    <p>{token ? "Authenticated simulation dashboard" : "Sign in above to enable live operations"}</p>
    <p role="status">{connected ? "Live WebSocket connected" : "Telemetry offline"}{error ? ` · ${error}` : ""}</p>
    <div style={{ overflowX: "auto" }}>
      <table><thead><tr><th>Robot</th><th>Status</th><th>X</th><th>Z</th><th>Progress</th><th>Replay</th></tr></thead>
        <tbody>{robots.map(r => <tr key={r.id}><td>{r.name}</td><td>{r.status}</td>
          <td>{r.position_x?.toFixed(2) ?? "—"}</td><td>{r.position_z?.toFixed(2) ?? "—"}</td>
          <td>{(r.movement_progress * 100).toFixed(0)}%</td>
          <td><button type="button" disabled={!token} onClick={() => void replayHistory(r.id)}>History</button></td>
        </tr>)}</tbody></table>
    </div>
    {robotId && <div><h4>Position replay</h4>
      <p>{history.length} saved snapshots</p>
      {selected && <p>At {new Date(selected.recorded_at).toLocaleString()}: X {selected.position_x.toFixed(2)}, Z {selected.position_z.toFixed(2)}, speed {selected.velocity.toFixed(2)}</p>}
      <input aria-label="Replay time" type="range" min={0} max={Math.max(0, history.length - 1)} value={replayIndex}
        onChange={e => setReplayIndex(Number(e.target.value))} disabled={history.length < 2} />
    </div>}
    <h4>Active mission controls</h4>
    {missions.filter(m => m.status === "in_progress").map(m => <div key={m.id}>
      <span>#{m.id.slice(0, 8)} {m.pickup_location} → {m.delivery_location} · {m.plan?.traffic_state ?? "unknown"} </span>
      <button type="button" onClick={() => void operate(m.id, "pause")}>Pause</button>
      <button type="button" onClick={() => void operate(m.id, "resume")}>Resume</button>
      <button type="button" onClick={() => void operate(m.id, "restart")}>Restart simulation</button>
    </div>)}
    <small>Simulated telemetry only. No physical collision protection or emergency stop.</small>
  </section>;
}


import { useMemo, useState } from "react";
import {
  Battery,
  Bot,
  CheckCircle2,
  Clock3,
  Cpu,
  MapPin,
  PlugZap,
  Search,
  ShieldAlert,
  Zap,
} from "lucide-react";

import type { Mission, Robot, RobotStatus } from "../types";

type RobotChange = Partial<
  Pick<Robot, "status" | "battery_level" | "current_location">
>;

type Props = {
  robots: Robot[];
  missions: Mission[];
  busy: string | null;
  onUpdate: (robot: Robot, changes: RobotChange) => void;
};

type Filter = "all" | RobotStatus;

const STATUS_LABELS: Record<RobotStatus, string> = {
  available: "Available",
  busy: "On mission",
  charging: "Charging",
  offline: "Offline",
  error: "Error",
};

const FILTERS: Filter[] = [
  "all",
  "available",
  "busy",
  "charging",
  "offline",
  "error",
];

function batteryColor(battery: number): string {
  if (battery < 30) return "#fb7185";
  if (battery < 60) return "#f9be63";
  return "#35e0c7";
}

function BatteryGauge({ level }: { level: number }) {
  const safeLevel = Math.max(0, Math.min(100, level));
  const color = batteryColor(safeLevel);

  return (
    <div
      className="fleet-battery-gauge"
      style={{
        background: `conic-gradient(
          ${color} ${safeLevel * 3.6}deg,
          #243650 0deg
        )`,
      }}
      aria-label={`Battery ${safeLevel}%`}
    >
      <div className="fleet-battery-inner">
        <Battery size={15} color={color} />
        <strong>{Math.round(safeLevel)}%</strong>
        <small>BATTERY</small>
      </div>
    </div>
  );
}

function RobotCard({
  robot,
  missions,
  busy,
  onUpdate,
}: {
  robot: Robot;
  missions: Mission[];
  busy: string | null;
  onUpdate: Props["onUpdate"];
}) {
  const activeMission = missions.find(
    mission =>
      mission.assigned_robot_id === robot.id &&
      (mission.status === "assigned" ||
        mission.status === "in_progress"),
  );

  const canActivate =
    robot.status !== "busy" &&
    robot.status !== "available" &&
    robot.battery_level >= 30 &&
    !!robot.current_location;

  const canCharge =
    robot.status === "available" ||
    robot.status === "offline" ||
    robot.status === "error";

  const isBusy = busy !== null;

  return (
    <article className={`fleet-robot-card robot-${robot.status}`}>
      <div className="fleet-card-top">
        <div className="fleet-robot-heading">
          <div className="fleet-robot-symbol">
            <Bot size={23} />
          </div>

          <div>
            <h3>{robot.name}</h3>
            <span className="fleet-robot-id">
              UNIT #{robot.id.slice(0, 8).toUpperCase()}
            </span>
          </div>
        </div>

        <span className={`fleet-card-status ${robot.status}`}>
          <span className="fleet-pulse-dot" />
          {STATUS_LABELS[robot.status]}
        </span>
      </div>

      <div className="fleet-card-content">
        <BatteryGauge level={robot.battery_level} />

        <div className="fleet-card-info">
          <div className="fleet-info-row">
            <span>
              <MapPin size={14} />
              Current station
            </span>
            <strong>
              {robot.current_location?.replace("STATION-", "") ??
                "Not set"}
            </strong>
          </div>

          <div className="fleet-info-row">
            <span>
              <Cpu size={14} />
              Operating mode
            </span>
            <strong>{STATUS_LABELS[robot.status]}</strong>
          </div>

          <div className="fleet-info-row">
            <span>
              <Clock3 size={14} />
              Last update
            </span>
            <strong>
              {new Date(robot.updated_at).toLocaleTimeString()}
            </strong>
          </div>
        </div>
      </div>

      <div className="fleet-assignment">
        {activeMission ? (
          <>
            <Zap size={16} />
            <div>
              <strong>Mission assigned</strong>
              <small>
                {activeMission.pickup_location.replace("STATION-", "")}
                {" → "}
                {activeMission.delivery_location.replace("STATION-", "")}
                {" · "}
                {activeMission.status.replace("_", " ")}
              </small>
            </div>
          </>
        ) : robot.status === "available" ? (
          <>
            <CheckCircle2 size={16} />
            <div>
              <strong>Ready for autonomous dispatch</strong>
              <small>Waiting for the next eligible mission</small>
            </div>
          </>
        ) : robot.status === "charging" ? (
          <>
            <PlugZap size={16} />
            <div>
              <strong>Charging mode</strong>
              <small>Excluded from mission selection</small>
            </div>
          </>
        ) : (
          <>
            <ShieldAlert size={16} />
            <div>
              <strong>Not available for dispatch</strong>
              <small>Check station, battery and operating state</small>
            </div>
          </>
        )}
      </div>

      <div className="fleet-card-actions">
        <button
          type="button"
          className="fleet-action-primary"
          disabled={!canActivate || isBusy}
          onClick={() => onUpdate(robot, { status: "available" })}
        >
          <CheckCircle2 size={15} />
          Mark available
        </button>

        <button
          type="button"
          className="fleet-action-secondary"
          disabled={!canCharge || isBusy}
          onClick={() => onUpdate(robot, { status: "charging" })}
        >
          <PlugZap size={15} />
          Set charging
        </button>
      </div>
    </article>
  );
}

export function RobotFleetView({
  robots,
  missions,
  busy,
  onUpdate,
}: Props) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const counts = useMemo(
    () => ({
      all: robots.length,
      available: robots.filter(r => r.status === "available").length,
      busy: robots.filter(r => r.status === "busy").length,
      charging: robots.filter(r => r.status === "charging").length,
      offline: robots.filter(r => r.status === "offline").length,
      error: robots.filter(r => r.status === "error").length,
    }),
    [robots],
  );

  const visible = useMemo(() => {
    const search = query.trim().toLowerCase();

    return robots
      .filter(r => filter === "all" || r.status === filter)
      .filter(r =>
        `${r.name} ${r.current_location ?? ""} ${r.status}`
          .toLowerCase()
          .includes(search),
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [robots, filter, query]);

  return (
    <section className="fleet-console">
      <div className="fleet-console-header">
        <div>
          <div className="fleet-section-eyebrow">
            FLEET OPERATIONS / REGISTERED UNITS
          </div>
          <h2>Autonomous Robot Fleet</h2>
          <p>
            Live operating status, battery readiness and mission
            assignments from PostgreSQL.
          </p>
        </div>

        <span className="fleet-live-label">
          <span className="fleet-pulse-dot" />
          {counts.all} REGISTERED UNITS
        </span>
      </div>

      <div className="fleet-filter-toolbar">
        <div className="fleet-filter-group">
          {FILTERS.map(item => (
            <button
              key={item}
              type="button"
              className={
                filter === item
                  ? "fleet-filter active"
                  : "fleet-filter"
              }
              onClick={() => setFilter(item)}
            >
              {item === "all" ? "All robots" : STATUS_LABELS[item]}
              <span>{counts[item]}</span>
            </button>
          ))}
        </div>

        <label className="fleet-search">
          <Search size={16} />
          <input
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Search robots or stations"
            aria-label="Search robots"
          />
        </label>
      </div>

      <div className="fleet-card-grid">
        {visible.map(robot => (
          <RobotCard
            key={robot.id}
            robot={robot}
            missions={missions}
            busy={busy}
            onUpdate={onUpdate}
          />
        ))}
      </div>

      {visible.length === 0 && (
        <div className="fleet-no-results">
          No robots match this search or filter.
        </div>
      )}
    </section>
  );
}

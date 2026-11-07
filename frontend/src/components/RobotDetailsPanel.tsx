import type { Mission, Robot } from "../types";

type Props = {
  robot: Robot;
  mission?: Mission;
  onClose: () => void;
};

export function RobotDetailsPanel({ robot, mission, onClose }: Props) {
  const coordinate = (n: number | null) => n === null ? "—" : n.toFixed(2);
  return (
    <aside className="warehouse-3d-robot-detail" aria-label={`Details for ${robot.name}`}>
      <button type="button" onClick={onClose} aria-label="Close robot details">×</button>
      <strong>{robot.name}</strong>
      <span>Unit: {robot.id.slice(0, 8).toUpperCase()}</span>
      <span>Status: {robot.status}</span>
      <span>Battery: {robot.battery_level.toFixed(1)}%</span>
      <span>Last station: {robot.current_location ?? "Unknown"}</span>
      <span>Simulated X/Z: {coordinate(robot.position_x)} / {coordinate(robot.position_z)}</span>
      <span>Progress: {(robot.movement_progress * 100).toFixed(0)}%</span>
      <span>Position updated: {robot.position_updated_at
        ? new Date(robot.position_updated_at).toLocaleTimeString()
        : "No telemetry yet"}</span>
      {mission && <>
        <span>Mission: #{mission.id.slice(0, 8).toUpperCase()}</span>
        <span>Task: {mission.pickup_location} → {mission.delivery_location}</span>
        <span>Mission status: {mission.status}</span>
      </>}
      <small>Simulated coordinates only — not physical robot localization.</small>
    </aside>
  );
}

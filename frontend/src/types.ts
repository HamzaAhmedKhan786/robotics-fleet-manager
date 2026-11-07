
export type RobotStatus =
  | "offline"
  | "available"
  | "busy"
  | "charging"
  | "error";

export type MissionStatus =
  | "pending"
  | "assigned"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "failed";

export type Robot = {
  id: string;
  name: string;
  status: RobotStatus;
  battery_level: number;
  current_location: string | null;
  created_at: string;
  updated_at: string;
};

export type MissionPlan = {
  path: string[];
  pickup_path: string[];
  delivery_path: string[];
  pickup_distance: number;
  delivery_distance: number;
  total_distance: number;
  battery_before: number;
  energy_required: number;
  battery_after: number;
  safety_reserve: number;
  duration_seconds: number;
  feasible: boolean;
  energy_model: string;
};

export type Mission = {
  id: string;
  pickup_location: string;
  delivery_location: string;
  priority: number;
  status: MissionStatus;
  assigned_robot_id: string | null;
  plan: MissionPlan | null;
  selection_reason: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type FleetSummary = {
  total_robots: number;
  active_robots: number;
  available_robots: number;
  charging_robots: number;
  offline_robots: number;
  total_missions: number;
  active_missions: number;
  pending_missions: number;
  completed_missions: number;
  robots_by_status: Record<RobotStatus, number>;
  missions_by_status: Record<MissionStatus, number>;
};

export type Warehouse = {
  stations: string[];
  edges: {
    source: string;
    target: string;
    distance: number;
  }[];
};

export type DemoResponse = {
  message: string;
  mission_ids: string[];
  robots_created: number;
  missions_created: number;
};

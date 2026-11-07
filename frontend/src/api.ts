
import type {
  DemoResponse,
  FleetSummary,
  Mission,
  Robot,
  Warehouse,
} from "./types";

const API_BASE = (
  import.meta.env.VITE_API_URL || ""
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      signal: init?.signal,
    });
  } catch {
    throw new ApiError(
      0,
      "Cannot connect to FastAPI. Start `pixi run backend`.",
    );
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);

    let detail = `Request failed (${response.status})`;

    if (
      typeof body === "object"
      && body !== null
      && "detail" in body
    ) {
      const value = (body as { detail: unknown }).detail;
      detail = typeof value === "string"
        ? value
        : JSON.stringify(value);
    }

    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export const api = {
  health: (signal?: AbortSignal) =>
    request<{ status: string }>("/health", { signal }),

  summary: (signal?: AbortSignal) =>
    request<FleetSummary>("/api/v1/fleet/summary", { signal }),

  warehouse: (signal?: AbortSignal) =>
    request<Warehouse>("/api/v1/fleet/warehouse", { signal }),

  robots: (signal?: AbortSignal) =>
    request<Robot[]>("/api/v1/robots", { signal }),

  missions: (signal?: AbortSignal) =>
    request<Mission[]>("/api/v1/missions", { signal }),

  createRobot: (
    data: {
      name: string;
      battery_level: number;
      current_location: string;
    },
  ) =>
    request<Robot>("/api/v1/robots", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateRobot: (
    id: string,
    data: Partial<
      Pick<Robot, "status" | "battery_level" | "current_location">
    >,
  ) =>
    request<Robot>(`/api/v1/robots/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  createMission: (
    data: {
      pickup_location: string;
      delivery_location: string;
      priority: number;
    },
  ) =>
    request<Mission>("/api/v1/missions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  missionAction: (
    id: string,
    action: "assign" | "start" | "complete" | "cancel",
  ) =>
    request<Mission>(`/api/v1/missions/${id}/${action}`, {
      method: "POST",
    }),

  demoSimulation: () =>
    request<DemoResponse>("/api/v1/demo/simulation", {
      method: "POST",
    }),
};

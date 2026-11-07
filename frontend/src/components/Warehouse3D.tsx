
import { useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import {
  Grid,
  Line,
  OrbitControls,
  Text,
} from "@react-three/drei";

import type { Mission, Robot, Warehouse } from "../types";
import { RobotCart3D } from "./RobotCart3D";
import type { Point3D } from "./RobotCart3D";
import { Station3D } from "./Station3D";
import { RobotDetailsPanel } from "./RobotDetailsPanel";

type Props = {
  warehouse: Warehouse;
  robots: Robot[];
  missions: Mission[];
};

const POSITIONS: Record<string, Point3D> = {
  "STATION-A1": [-6, 0, -4],
  "STATION-A2": [0, 0, -4],
  "STATION-A3": [6, 0, -4],
  "STATION-B1": [-6, 0, 4],
  "STATION-B2": [0, 0, 4],
  "STATION-B3": [6, 0, 4],
};

const COLORS = [
  "#39ead1",
  "#b39bff",
  "#ffbc6c",
  "#6ab5ff",
  "#ff87b0",
  "#b4f16c",
];

function normalizeStation(station?: string | null): string {
  if (!station) return "";

  return station.startsWith("STATION-")
    ? station
    : `STATION-${station}`;
}

function getPosition(station?: string | null) {
  return POSITIONS[normalizeStation(station)];
}

function StorageRack({
  position,
}: {
  position: Point3D;
}) {
  return (
    <group position={position}>
      {/* Steel frame */}
      {[-0.95, 0.95].flatMap(x =>
        [-0.5, 0.5].map(z => (
          <mesh
            key={`${x}-${z}`}
            position={[x, 1.3, z]}
            castShadow
          >
            <boxGeometry args={[0.08, 2.6, 0.08]} />
            <meshStandardMaterial
              color="#5888a5"
              metalness={0.85}
              roughness={0.3}
            />
          </mesh>
        )),
      )}

      {/* Four storage levels */}
      {[0.3, 1.05, 1.8, 2.55].map(height => (
        <mesh
          key={height}
          position={[0, height, 0]}
          receiveShadow
        >
          <boxGeometry args={[2.05, 0.075, 1.12]} />
          <meshStandardMaterial
            color="#244d65"
            metalness={0.75}
            roughness={0.32}
          />
        </mesh>
      ))}
    {/* Warehouse cartons */}
    {[0.66, 1.41, 2.16].flatMap(height =>
        [-0.48, 0.48].map(x => (
            <mesh
            key={`${height}-${x}`}
            position={[x, height, 0]}
            castShadow
            >
            <boxGeometry args={[0.79, 0.47, 0.78]} />
            <meshStandardMaterial
                color="#bd8853"
                roughness={0.8}
            />
            </mesh>
        ))
    )}
    </group>
  );
}

function WarehouseScene({
  warehouse,
  robots,
  missions,
  selectedRobotId,
  onSelectRobot,
  showRoutes,
}: Props & {
  selectedRobotId: string | null;
  onSelectRobot: (id: string) => void;
  showRoutes: boolean;
}) {
  const activeMissions = useMemo(
    () =>
      missions
        .filter(
          mission =>
            mission.status === "assigned" ||
            mission.status === "in_progress",
        )
        .sort((a, b) => a.id.localeCompare(b.id)),
    [missions],
  );

  // Give parked robots small offsets if they share a station.
  const placedRobots = useMemo(() => {
    const occupied: Record<string, number> = {};

    return robots.flatMap(robot => {
      const station = normalizeStation(robot.current_location);
      const base = getPosition(station);

      if (!base) return [];

      const slot = occupied[station] ?? 0;
      occupied[station] = slot + 1;

      const column = slot % 3;
      const row = Math.floor(slot / 3);

      return [{
        robot,
        position: [
          base[0] + (column - 1) * 1.25,
          0,
          base[2] + 1.45 + row * 1.2,
        ] as Point3D,
      }];
    });
  }, [robots]);

  return (
    <>
      <color attach="background" args={["#061523"]} />

      <ambientLight intensity={1.6} />

      <hemisphereLight
        args={["#c7eaff", "#102338", 1.5]}
      />

      <directionalLight
        position={[10, 16, 8]}
        intensity={2.4}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      <pointLight
        position={[0, 8, 0]}
        intensity={48}
        color="#44cddd"
        distance={32}
      />

      {/* Warehouse floor */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.12, 0]}
        receiveShadow
      >
        <planeGeometry args={[24, 19]} />
        <meshStandardMaterial
          color="#102638"
          roughness={0.6}
          metalness={0.32}
        />
      </mesh>

      <Grid
        position={[0, -0.065, 0]}
        args={[24, 19]}
        cellSize={1}
        cellColor="#294f69"
        sectionSize={5}
        sectionColor="#397e98"
        fadeDistance={40}
        infiniteGrid={false}
      />

      {/* Racks: outside the main station connections */}
      {[-9.3, -3, 3, 9.3].flatMap(x =>
        [-7, 0, 7].map(z => (
          <StorageRack
            key={`${x}-${z}`}
            position={[x, 0, z]}
          />
        )),
      )}

      {/* General warehouse connection graph */}
      {warehouse.edges.map(edge => {
        const start = getPosition(edge.source);
        const end = getPosition(edge.target);

        if (!start || !end) return null;

        return (
          <Line
            key={`${edge.source}-${edge.target}`}
            points={[
              [start[0], 0.11, start[2]],
              [end[0], 0.11, end[2]],
            ]}
            color="#3a6f8b"
            lineWidth={3}
            transparent
            opacity={0.75}
          />
        );
      })}

      {/* Active mission routes */}
      {showRoutes && activeMissions.map((mission, index) => {
        const route = (mission.plan?.path ?? [])
          .map(station => getPosition(station))
          .filter(
            (point): point is Point3D => Boolean(point),
          );

        if (route.length < 2) return null;

        const selected =
          mission.assigned_robot_id === selectedRobotId;

        return (
          <Line
            key={mission.id}
            points={route.map(
              ([x, , z]) =>
                [x, 0.22 + index * 0.055, z] as Point3D,
            )}
            color={COLORS[index % COLORS.length]}
            lineWidth={selected ? 8 : 5}
            transparent
            opacity={selected ? 1 : 0.88}
          />
        );
      })}

      {/* Stations */}
      {warehouse.stations.map(station => {
        const position = getPosition(station);

        if (!position) return null;

        return (
          <Station3D
            key={station}
            name={station}
            position={position}
          />
        );
      })}

      {/* Simulated AMR carts */}
      {placedRobots.map(({ robot, position }) => {
        const cartPosition: Point3D =
          robot.status === "busy" && robot.position_x !== null && robot.position_z !== null
            ? [robot.position_x, 0, robot.position_z]
            : position;

        return (
          <RobotCart3D
            key={robot.id}
            robot={robot}
            position={cartPosition}
            selected={robot.id === selectedRobotId}
            onSelect={onSelectRobot}
          />
        );
      })}

      {/* Warehouse heading in 3D */}
      <Text
        position={[0, 0.03, -8.8]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.55}
        color="#548aa4"
      >
        FLEETOS — AUTONOMOUS WAREHOUSE
      </Text>

      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        target={[0, 0.4, 0]}
        minDistance={8}
        maxDistance={36}
        maxPolarAngle={Math.PI / 2.05}
      />
    </>
  );
}

export function Warehouse3D({
  warehouse,
  robots,
  missions,
}: Props) {
  const [selectedRobotId, setSelectedRobotId] =
    useState<string | null>(null);

  const [showRoutes, setShowRoutes] = useState(true);

  const selectedRobot =
    robots.find(robot => robot.id === selectedRobotId) ?? null;

  const activeMissions = missions.filter(
    mission =>
      mission.status === "assigned" ||
      mission.status === "in_progress",
  );

  return (
    <section className="warehouse-3d">
      <div className="warehouse-3d-header">
        <div>
          <span className="warehouse-3d-eyebrow">
            DIGITAL TWIN / AUTONOMOUS OPERATIONS
          </span>
          <h3>3D Warehouse & Robot Fleet</h3>
        </div>

        <div className="warehouse-3d-tools">
          <span>{robots.length} robots</span>
          <span>{activeMissions.length} active missions</span>
        </div>
      </div>

      <div className="warehouse-3d-viewport">
        <Canvas
          shadows
          camera={{
            position: [13, 15, 18],
            fov: 40,
            near: 0.1,
            far: 100,
          }}
          dpr={[1, 2]}
        >
          <WarehouseScene
            warehouse={warehouse}
            robots={robots}
            missions={missions}
            showRoutes={showRoutes}
            selectedRobotId={selectedRobotId}
            onSelectRobot={setSelectedRobotId}
            />
        </Canvas>

        <div className="warehouse-3d-overlay">
          <label>
            <input
              type="checkbox"
              checked={showRoutes}
              onChange={event =>
                setShowRoutes(event.target.checked)
              }
            />
            Show mission routes
          </label>

          <div className="warehouse-3d-legend">
            <span>🟢 Available</span>
            <span>🟣 Busy</span>
            <span>🟡 Charging</span>
          </div>
        </div>

        {selectedRobot && (
          <RobotDetailsPanel
            robot={selectedRobot}
            mission={activeMissions.find(m => m.assigned_robot_id === selectedRobot.id)}
            onClose={() => setSelectedRobotId(null)}
          />
        )}
      </div>

      <div className="warehouse-3d-footer">
        <span>
          Drag: rotate · Scroll: zoom · Right-drag: pan
        </span>
        <span>
          Robot movement: backend snapshots calculated in Rust
        </span>
      </div>
    </section>
  );
}

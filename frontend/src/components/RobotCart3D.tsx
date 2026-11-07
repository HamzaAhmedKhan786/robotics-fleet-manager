
import { useFrame } from "@react-three/fiber";
import { Text } from "@react-three/drei";
import { useRef } from "react";
import * as THREE from "three";

import type { Robot } from "../types";

export type Point3D = [number, number, number];

type Props = {
  robot: Robot;
  position: Point3D;
  selected?: boolean;
  onSelect?: (robotId: string) => void;
};

const STATUS_COLORS: Record<Robot["status"], string> = {
  available: "#38e9c9",
  busy: "#aa96ff",
  charging: "#ffbe63",
  offline: "#8190a4",
  error: "#ff6583",
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function RobotCart3D({
  robot,
  position,
  selected = false,
  onSelect,
}: Props) {
  const group = useRef<THREE.Group>(null);

  const color = STATUS_COLORS[robot.status];
  useFrame((_, delta) => {
    const object = group.current;
    if (!object) return;
    // Backend position is authoritative; React only smooths snapshots.
    const target = position;

    const smoothing = 1 - Math.exp(-delta * 9);

    const previousX = object.position.x;
    const previousZ = object.position.z;

    object.position.x = THREE.MathUtils.lerp(
      object.position.x,
      target[0],
      smoothing,
    );
    object.position.y = THREE.MathUtils.lerp(
      object.position.y,
      target[1],
      smoothing,
    );
    object.position.z = THREE.MathUtils.lerp(
      object.position.z,
      target[2],
      smoothing,
    );

    const dx = object.position.x - previousX;
    const dz = object.position.z - previousZ;

    if (Math.hypot(dx, dz) > 0.0001) {
      const angle = Math.atan2(dx, dz);
      object.rotation.y = THREE.MathUtils.lerp(
        object.rotation.y,
        angle,
        smoothing,
      );
    }
  });

  return (
    <group
      ref={group}
      position={position}
      onClick={event => {
        event.stopPropagation();
        onSelect?.(robot.id);
      }}
    >
      {/* Selection ring */}
      {selected && (
        <mesh
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, 0.06, 0]}
        >
          <ringGeometry args={[0.76, 0.85, 48]} />
          <meshBasicMaterial
            color="#ffffff"
            side={THREE.DoubleSide}
          />
        </mesh>
      )}

      {/* Robot shadow/base */}
      <mesh position={[0, 0.14, 0]}>
        <boxGeometry args={[1.06, 0.22, 0.83]} />
        <meshStandardMaterial
          color="#111d29"
          metalness={0.6}
          roughness={0.45}
        />
      </mesh>

      {/* Orange autonomous cart chassis */}
      <mesh castShadow position={[0, 0.37, 0]}>
        <boxGeometry args={[0.98, 0.32, 0.78]} />
        <meshStandardMaterial
          color="#f29c45"
          metalness={0.45}
          roughness={0.33}
        />
      </mesh>

      {/* Cargo platform */}
      <mesh castShadow position={[0, 0.58, 0]}>
        <boxGeometry args={[0.76, 0.13, 0.64]} />
        <meshStandardMaterial
          color="#34495d"
          metalness={0.6}
          roughness={0.3}
        />
      </mesh>

      {/* Sensor / navigation unit */}
      <mesh position={[0, 0.75, 0]}>
        <cylinderGeometry args={[0.13, 0.17, 0.23, 12]} />
        <meshStandardMaterial
          color="#22374a"
          metalness={0.65}
        />
      </mesh>

      <mesh position={[0, 0.88, 0]}>
        <sphereGeometry args={[0.10, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1.8}
        />
      </mesh>

      {/* Four wheels */}
      {[-0.42, 0.42].flatMap(x =>
        [-0.29, 0.29].map(z => (
          <mesh
            key={`${x}-${z}`}
            position={[x, 0.16, z]}
            rotation={[0, 0, Math.PI / 2]}
          >
            <cylinderGeometry args={[0.17, 0.17, 0.13, 16]} />
            <meshStandardMaterial
              color="#0a111a"
              roughness={0.85}
            />
          </mesh>
        )),
      )}

      {/* Front sensor */}
      <mesh position={[0, 0.35, 0.405]}>
        <boxGeometry args={[0.44, 0.08, 0.045]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1.2}
        />
      </mesh>

      {/* Battery bar */}
      <mesh position={[0, 0.675, 0]}>
        <boxGeometry args={[0.48, 0.025, 0.12]} />
        <meshBasicMaterial color="#172635" />
      </mesh>

      <mesh
        position={[
          -0.24 + (clamp(robot.battery_level, 0, 100) / 100) * 0.24,
          0.696,
          0,
        ]}
      >
        <boxGeometry
          args={[
            Math.max(
              0.001,
              (clamp(robot.battery_level, 0, 100) / 100) * 0.48,
            ),
            0.025,
            0.10,
          ]}
        />
        <meshBasicMaterial
          color={
            robot.battery_level < 30 ? "#ff6b87" : "#47eed0"
          }
        />
      </mesh>

      {/* Floating robot label */}
      <Text
        position={[0, 1.44, 0]}
        fontSize={0.23}
        color={selected ? "#ffffff" : "#d9eff9"}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.012}
        outlineColor="#081725"
      >
        {robot.name}
      </Text>

      <Text
        position={[0, 1.14, 0]}
        fontSize={0.18}
        color={color}
        anchorX="center"
        anchorY="middle"
      >
        {`${Math.round(robot.battery_level)}% · ${robot.status}`}
      </Text>
    </group>
  );
}

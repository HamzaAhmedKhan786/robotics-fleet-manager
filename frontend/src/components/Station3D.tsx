
import { Text } from "@react-three/drei";
import * as THREE from "three";

import type { Point3D } from "./RobotCart3D";

type Props = {
  name: string;
  position: Point3D;
  highlighted?: boolean;
  onSelect?: (station: string) => void;
};

export function Station3D({
  name,
  position,
  highlighted = false,
  onSelect,
}: Props) {
  const color = highlighted ? "#ffcf78" : "#39ebd6";

  return (
    <group
      position={position}
      onClick={event => {
        event.stopPropagation();
        onSelect?.(name);
      }}
    >
      {/* Ground plate */}
      <mesh receiveShadow position={[0, 0.04, 0]}>
        <cylinderGeometry args={[0.85, 0.85, 0.08, 48]} />
        <meshStandardMaterial
          color="#142c43"
          metalness={0.55}
          roughness={0.4}
        />
      </mesh>

      {/* Illuminated outer ring */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.10, 0]}
      >
        <ringGeometry args={[0.69, 0.77, 48]} />
        <meshBasicMaterial
          color={color}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Center pad */}
      <mesh position={[0, 0.095, 0]}>
        <cylinderGeometry args={[0.50, 0.50, 0.04, 32]} />
        <meshStandardMaterial
          color={highlighted ? "#56462f" : "#17485a"}
          emissive={highlighted ? "#715126" : "#06627a"}
          emissiveIntensity={0.65}
        />
      </mesh>

      {/* Corner signal columns */}
      {[
        [-0.9, -0.9],
        [0.9, -0.9],
        [-0.9, 0.9],
        [0.9, 0.9],
      ].map(([x, z]) => (
        <group key={`${x}-${z}`} position={[x, 0, z]}>
          <mesh position={[0, 0.35, 0]}>
            <cylinderGeometry args={[0.055, 0.055, 0.7, 8]} />
            <meshStandardMaterial color="#35576d" />
          </mesh>

          <mesh position={[0, 0.73, 0]}>
            <sphereGeometry args={[0.075, 10, 10]} />
            <meshStandardMaterial
              color={color}
              emissive={color}
              emissiveIntensity={1.3}
            />
          </mesh>
        </group>
      ))}

      <Text
        position={[0, 1.65, 0]}
        fontSize={0.44}
        color="#f0fbff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#071523"
      >
        {name.replace("STATION-", "")}
      </Text>

      <Text
        position={[0, 1.29, 0]}
        fontSize={0.14}
        color={color}
        anchorX="center"
        anchorY="middle"
      >
        WAREHOUSE STATION
      </Text>
    </group>
  );
}

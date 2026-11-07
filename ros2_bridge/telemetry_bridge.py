"""Read-only ROS 2 telemetry bridge for the FleetOS simulator.

Requires a ROS 2 Python environment with rclpy, std_msgs, and httpx.
Publishes simulated snapshots on /fleetos/simulated_fleet (std_msgs/String).
DO NOT connect this demonstration bridge to hardware motion-control topics.
"""
import json
import os

import httpx
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class FleetOSTelemetryBridge(Node):
    def __init__(self):
        super().__init__("fleetos_simulated_telemetry_bridge")
        self.publisher = self.create_publisher(String, "/fleetos/simulated_fleet", 10)
        self.client = httpx.Client(timeout=5)
        self.url = os.environ.get("FLEETOS_API_URL", "http://127.0.0.1:8000")
        self.create_timer(1.0, self.poll)

    def poll(self):
        try:
            result = self.client.get(self.url + "/api/v1/robots")
            result.raise_for_status()
            payload = String()
            payload.data = json.dumps({"source": "fleetos_simulation", "robots": result.json()})
            self.publisher.publish(payload)
        except (httpx.HTTPError, ValueError) as exc:
            self.get_logger().warning(f"FleetOS telemetry unavailable: {exc}")

    def destroy_node(self):
        self.client.close()
        return super().destroy_node()


def main():
    rclpy.init()
    node = FleetOSTelemetryBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

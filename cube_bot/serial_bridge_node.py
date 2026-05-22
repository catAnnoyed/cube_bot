import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
import serial

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge_node')
        self.subscription = self.create_subscription(
            Int32MultiArray,
            'motor_speeds',
            self.listener_callback,
            10)
        
        # Adjust serial port config as necessary ('COM3', '/dev/ttyUSB0', etc.)
        self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        self.get_logger().info("Serial Bridge Array Node Online.")

    def listener_callback(self, msg):
        if len(msg.data) == 2:
            left_speed = msg.data[0]
            right_speed = msg.data[1]
            
            # Format data to CSV string payload
            payload = f"{left_speed},{right_speed}\n"
            
            # Write to Arduino
            self.serial_port.write(payload.encode('utf-8'))
            self.get_logger().info(f"Sent Speeds -> Left: {left_speed} | Right: {right_speed}")

def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.serial_port.close()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
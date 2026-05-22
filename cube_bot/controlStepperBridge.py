import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial
import time

class RosToArduinoButtonBridge(Node):
    def __init__(self):
        super().__init__('ros_to_arduino_button_bridge')
        
        # Open Serial connection to Nano (Adjust port if on Windows, e.g., 'COM3')
        self.arduino = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=0.1)
        time.sleep(2) 
        
        # Subscribe to the BUTTONS topic
        self.subscription = self.create_subscription(
            Int32,
            '/controller_buttons_topic',
            self.listener_callback,
            10)
        
        self.get_logger().info("Button Serial Bridge Node Started.")

    def listener_callback(self, msg):
        # msg.data is just the raw bitmask integer (e.g., 0, 1, 8, etc.)
        button_mask = msg.data
        
        # Send the integer as a text packet followed by a newline character
        packet = f"{button_mask}\n"
        self.arduino.write(packet.encode('utf-8'))

def main(args=None):
    rclpy.init(args=args)
    bridge = RosToArduinoButtonBridge()
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.arduino.close()
        bridge.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
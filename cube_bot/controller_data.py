import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Int32MultiArray
from sensor_msgs.msg import Joy

class ControllerDataNode(Node):
    def __init__(self):
        super().__init__('controller_data_node')
        
        # Subscribe to live raw PS4 data
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        
        # Publisher for combined driving coordinates [Y, X, Phase_Button]
        self.formatted_joy_pub = self.create_publisher(Int32MultiArray, '/controller_input_topic', 10)
        
        # Publisher for the 3-state grabber topic
        self.grabber_pub = self.create_publisher(Int32, '/grabber_command_topic', 10)

        self.get_logger().info("Controller Logic Node active. 3-State Topic Mode operational.")

    def joy_callback(self, msg):
        # 1. DRIVING LOGIC (Single Left Stick Mapping)
        stick_y = int(msg.axes[1] * 100)  # Forward/Backward
        stick_x = int(msg.axes[0] * 100)  # Left/Right turning
        toggle_phase_btn = msg.buttons[2] # Triangle Button
        
        formatted_msg = Int32MultiArray()
        formatted_msg.data = [stick_y, stick_x, toggle_phase_btn]
        self.formatted_joy_pub.publish(formatted_msg)

        # 2. GRABBER LOGIC (3-State Integer Mapping)
        pickup_btn = msg.buttons[3]  # Square
        putdown_btn = msg.buttons[0] # X

        # Establish our default state
        grabber_state = 0  # 0 = Neutral (No buttons pressed)

        if pickup_btn == 1:
            grabber_state = 1  # 1 = Grab Command Active
        elif putdown_btn == 1:
            grabber_state = 2  # 2 = Retract Command Active

        # Continuously broadcast the exact state of your thumb buttons
        grab_msg = Int32()
        grab_msg.data = grabber_state
        self.grabber_pub.publish(grab_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ControllerDataNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

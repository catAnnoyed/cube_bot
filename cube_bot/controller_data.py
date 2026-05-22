import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, Int32MultiArray
from sensor_msgs.msg import Joy

class ControllerDataNode(Node):
    def __init__(self):
        super().__init__('controller_data_node')
        
        # Subscribe to live raw PS4 data
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        
        # Publisher for joystick coordinate
        self.formatted_joy_pub = self.create_publisher(Int32MultiArray, '/controller_joy_topic', 10)
        
        # Publisher to controller buttons
        self.buttons_pub = self.create_publisher(Int32, '/controller_buttons_topic', 10)

        self.get_logger().info("Controller Logic Node active.")

    def joy_callback(self, msg):
        # joytisck (you get value -100 to 100)
        stick_y = int(msg.axes[1] * 100)  # Forward/Backward
        stick_x = int(msg.axes[0] * 100)  # Left/Right turning
        formatted_msg = Int32MultiArray()
        formatted_msg.data = [stick_y, stick_x]
        self.formatted_joy_pub.publish(formatted_msg)

        #buttons
        btn1 = msg.buttons[0]  # A
        btn2 = msg.buttons[1]  # B
        btn3 = msg.buttons[2]  # X
        btn4 = msg.buttons[3]  # Y
       
        bttn_state = 0
        if btn1 == 1: bttn_state |= (1 << 0) # 0001
        if btn2 == 1: bttn_state |= (1 << 1) # 0010
        if btn3 == 1: bttn_state |= (1 << 2) # 0100
        if btn4 == 1: bttn_state |= (1 << 3) # 1000
       
       bttn_msg = Int32()
       bttn_msg.data = bttn_state
       self.buttons_pub.publish(bttn_msg)


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

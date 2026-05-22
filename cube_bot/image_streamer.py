import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

class ImageStreamerNode(Node):
    def __init__(self):
        super().__init__('image_streamer_node')
        
        # Publisher to stream raw frames to the processing node
        self.image_pub = self.create_publisher(Image, '/robot/camera/image_raw', 10)
        
        # Initialize the CV Bridge translator
        self.bridge = CvBridge()
        
        # YOUR EXACT VIDEO CAPTURE DEFINITION
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            self.get_logger().error("Could not open camera device 0. Is it plugged in?")
            
        # Create a timer to capture frames at roughly 30 FPS
        self.create_timer(1.0 / 30.0, self.stream_frame)
        self.get_logger().info("Image Streamer active. Publishing raw video feed...")

    def stream_frame(self):
        # YOUR EXACT FRAME CAPTURE LINE
        ret, frame = self.cap.read()
        
        if ret:
            # Convert the raw OpenCV frame into a ROS 2 Image message
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            
            # Publish it over the network to the processing node
            self.image_pub.publish(ros_image)
        else:
            self.get_logger().warn("Failed to grab hardware frame from camera.")

    def destroy_node(self):
        # Clean up the hardware capture interface safely
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ImageStreamerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

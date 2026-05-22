import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

class IPAndPhoneCameraStreamer(Node):
    def __init__(self):
        super().__init__('image_streamer_node')
        
        # 1. Define the Master Publisher for your CNN node to listen to
        self.image_pub = self.create_publisher(Image, '/robot/camera/image_raw', 10)
        self.bridge = CvBridge()
        
        # 2. Drop your phone's IP camera network URL feed straight in here
        # (Make sure your Pi and Phone are logged into the exact same Wi-Fi network!)
        self.camera_url = "http://10.164.64.126:8080/video"
        
        self.get_logger().info(f"Connecting to phone camera feed at: {self.camera_url}")
        self.cap = cv2.VideoCapture(self.camera_url)
        
        if not self.cap.isOpened():
            self.get_logger().error("CRITICAL: Could not open the phone camera network stream!")
            return

        # 3. Create a high-speed execution timer loop (runs approx 30 frames per second)
        self.timer = self.create_timer(1.0 / 30.0, self.timer_callback)
        self.get_logger().info("Phone camera stream successfully hooked into ROS 2 network.")

    def timer_callback(self):
        ret, frame = self.cap.read()
        
        if ret:
            try:
                # Optional: Resize the raw phone feed if it is laggy on the network
                # A standard 640x480 resolution keeps the Wi-Fi latency very low
                # frame = cv2.resize(frame, (640, 480))
                
                # Convert OpenCV frame matrix directly into a ROS 2 Image message
                ros_image_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                
                # Fire it out across the global topic highway
                self.image_pub.publish(ros_image_msg)
                
            except Exception as e:
                self.get_logger().error(f"Failed to bridge video compression: {str(e)}")
        else:
            self.get_logger().warn("Dropped frame or slow Wi-Fi packet detected from phone connection...")

    def destroy_node(self):
        # Clean up the hardware capture channel when shutting down
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = IPAndPhoneCameraStreamer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

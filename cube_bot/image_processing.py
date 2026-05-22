import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String # To send F, L, R commands
import cv2
from cv_bridge import CvBridge

class ImageProcessorNode(Node):
    def __init__(self):
        super().__init__('image_processor_node')
        
        # Subscriber for the RAW image stream from the source node
        self.image_sub = self.create_subscription(Image, '/robot/camera/image_raw', self.image_callback, 10)
        
        # Publisher to send F, L, R data to the Main Brain
        self.command_pub = self.create_publisher(String, '/tracking_command', 10)
        
        self.bridge = CvBridge()
        
        # Set up your trackbars and calibration constants
        # cv2.namedWindow("Trackbars")
        # cv2.createTrackbar("Threshold", "Trackbars", 120, 255, lambda x: None)
        # cv2.createTrackbar("Center", "Trackbars", 0, 255, lambda x: None)
        self.frameCenter = 320
        self.static_threshold = 120
        self.static_center_offset = 25
        
        self.get_logger().info("Image Processor Node active. Waiting for raw frames...")

    def image_callback(self, msg):
        try:
            # 1. Convert ROS 2 Image message to OpenCV format
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            
            # =======================================================
            # YOUR EXACT PROCESSING LOGIC
            # =======================================================
            
            # Resize
            frame = cv2.resize(frame, (640, 480))

            # Use only bottom area
            roi = frame[350:480, 0:640]

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # Read trackbar values
            centerCalibration_val = cv2.getTrackbarPos("Center", "Trackbars")
            leftCalibration = self.frameCenter - centerCalibration_val
            rightCalibration = self.frameCenter + centerCalibration_val
            thresh_val = cv2.getTrackbarPos("Threshold", "Trackbars")

            # Threshold
            _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)

            # Draw calibration lines
            cv2.line(thresh, (leftCalibration, 0), (leftCalibration, 130), 128, 2)
            cv2.line(thresh, (rightCalibration, 0), (rightCalibration, 130), 128, 2)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                c = max(contours, key=cv2.contourArea)
                M = cv2.moments(c)

                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    
                    # Instead of arduino.write(), package the command into a ROS message
                    cmd_msg = String()

                    if cx < leftCalibration:
                        self.get_logger().info("Processed Command: Left")
                        cmd_msg.data = "L\n"

                    elif cx > rightCalibration:
                        self.get_logger().info("Processed Command: Right")
                        cmd_msg.data = "R\n"

                    else:
                        self.get_logger().info("Processed Command: Forward")
                        cmd_msg.data = "F\n"
                        
                    # Send the character command to the Main Brain
                    self.command_pub.publish(cmd_msg)

            # Standardized viewing (make waitKey(1) short)
            cv2.imshow("Tracking View (Thresh)", thresh)
            cv2.imshow("Main view", frame)
            cv2.waitKey(1) 

        except Exception as e:
            self.get_logger().error(f"Image processing failure: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()


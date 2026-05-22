import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32MultiArray
import cv2
from cv_bridge import CvBridge

class LineFollowerVisionNode(Node):
    def __init__(self):
        super().__init__('line_follower_vision_node')
        
        # 1. Initialize CvBridge
        self.bridge = CvBridge()
        
        # 2. Subscribe to the raw image topic coming from your streamer node
        self.image_sub = self.create_subscription(
            Image, 
            '/robot/camera/image_raw', 
            self.image_callback, 
            10
        )
        
        # 3. Keep the Motor speed publisher going out to the Serial Bridge
        self.publisher_ = self.create_publisher(Int32MultiArray, 'motor_speeds', 10)
        
        # 4. Setup OpenCV Trackbars and state variables
        cv2.namedWindow("Trackbars")
        cv2.createTrackbar("Threshold", "Trackbars", 120, 255, lambda x: None)
        cv2.createTrackbar("Kp (x0.01)", "Trackbars", 50, 200, lambda x: None)
        cv2.createTrackbar("Ki (x0.001)", "Trackbars", 0, 100, lambda x: None)
        cv2.createTrackbar("Kd (x0.01)", "Trackbars", 10, 200, lambda x: None)

        self.frameCenter = 320
        self.integral = 0
        self.last_error = 0
        self.base_speed = 150
        self.robot_state = "TRACKING"
        
        self.get_logger().info("LineFollowerVisionNode initialized. Waiting for image frames...")

    def image_callback(self, msg):
        try:
            # Convert ROS 2 Image message straight back into standard OpenCV BGR format
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to bridge incoming image: {str(e)}")
            return

        # --- LINE FOLLOWER CORE VISUALLY PROCESSING PIPELINE ---
        frame = cv2.resize(frame, (640, 480))
        roi = frame[350:480, 0:640]  # 130px height, 640px width
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        thresh_val = cv2.getTrackbarPos("Threshold", "Trackbars")
        _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)

        cv2.line(thresh, (self.frameCenter, 0), (self.frameCenter, 130), 128, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        left_motor_speed = self.base_speed
        right_motor_speed = self.base_speed

        if self.robot_state == "TRACKING":
            if contours:
                c = max(contours, key=cv2.contourArea)
                M = cv2.moments(c)
                x, y, w, h = cv2.boundingRect(c)

                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    error = cx - self.frameCenter

                    # Sharp Turn Detection
                    if error < -150 and w > 250:
                        self.get_logger().info("Sharp Left Intersection! Switching state...")
                        self.robot_state = "SHARP_LEFT"
                        return
                    elif error > 150 and w > 250:
                        self.get_logger().info("Sharp Right Intersection! Switching state...")
                        self.robot_state = "SHARP_RIGHT"
                        return

                    # PID Math
                    Kp = cv2.getTrackbarPos("Kp (x0.01)", "Trackbars") / 100.0
                    Ki = cv2.getTrackbarPos("Ki (x0.001)", "Trackbars") / 1000.0
                    Kd = cv2.getTrackbarPos("Kd (x0.01)", "Trackbars") / 100.0

                    self.integral = max(min(self.integral + error, 1000), -1000)
                    derivative = error - self.last_error
                    pid_output = (Kp * error) + (Ki * self.integral) + (Kd * derivative)
                    self.last_error = error

                    left_motor_speed = self.base_speed + pid_output
                    right_motor_speed = self.base_speed - pid_output
            else:
                self.get_logger().warn("Line lost!")

        elif self.robot_state == "SHARP_LEFT":
            left_motor_speed = -80
            right_motor_speed = 120
            if contours:
                c = max(contours, key=cv2.contourArea)
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    if 220 < cx < 420:
                        self.robot_state = "TRACKING"
                        self.integral = 0
                        self.last_error = 0

        elif self.robot_state == "SHARP_RIGHT":
            left_motor_speed = 120
            right_motor_speed = -80
            if contours:
                c = max(contours, key=cv2.contourArea)
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    if 220 < cx < 420:
                        self.robot_state = "TRACKING"
                        self.integral = 0
                        self.last_error = 0

        # Constraints
        left_motor_speed = max(min(int(left_motor_speed), 255), -255)
        right_motor_speed = max(min(int(right_motor_speed), 255), -255)

        # ─── PUBLISH THE CALCULATED SPEEDS ───
        msg_speeds = Int32MultiArray()
        msg_speeds.data = [left_motor_speed, right_motor_speed]
        self.publisher_.publish(msg_speeds)

        # UI Diagnostics Windows
        cv2.imshow("Line", thresh)
        cv2.imshow("Frame", frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = LineFollowerVisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
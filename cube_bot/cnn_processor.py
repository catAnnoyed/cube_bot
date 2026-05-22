import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String
import cv2
from cv_bridge import CvBridge
import torch
import torchvision.transforms as transforms
import numpy as np

# Import the class model defined above (assumed to be in your package or pasted locally)
# from cube_bot.model_definition import MultiTaskLineAndLetterCNN

class CNNProcessorNode(Node):
    def __init__(self):
        super().__init__('cnn_processor_node')
        
        # --- Publishers & Subscribers ---
        self.image_sub = self.create_subscription(Image, '/robot/camera/image_raw', self.image_callback, 10)
        self.error_pub = self.create_publisher(Float32, '/line/cross_track_error', 10)
        self.letter_pub = self.create_publisher(String, '/cube/detected_letter', 10)
        
        self.bridge = CvBridge()
        
        # --- Load Neural Network Model ---
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Using the class we built in Part 1
        from cube_bot.cnn_processor import MultiTaskLineAndLetterCNN # Self-reference fallback
        self.model = MultiTaskLineAndLetterCNN().to(self.device)
        
        model_path = '/home/ubuntu/ros2_ws/src/cube_bot/models/multitask_line_model.pth'
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            self.get_logger().info("Multi-Task CNN Model initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to load CNN weights file: {str(e)}")

        # --- Pre-processing Image Transforms ---
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((120, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.letter_map = {0: "None", 1: "A", 2: "B", 3: "C"}

    def image_callback(self, msg):
        try:
            # 1. Convert ROS image message to standard OpenCV matrix
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            
            # 2. Transform the frame for PyTorch tensor formatting
            tensor_img = self.transform(frame).unsqueeze(0).to(self.device)
            
            # 3. Disable gradients and compute prediction vectors
            with torch.no_grad():
                pred_error, pred_letter_logits = self.model(tensor_img)
                
                # Extract the continuous error float
                calculated_error = float(pred_error.item())
                
                # Extract the high-score index for the letter category classification
                _, letter_idx = torch.max(pred_letter_logits, 1)
                detected_letter = self.letter_map[letter_idx.item()]

            # 4. Publish the Continuous Error Float
            error_msg = Float32()
            error_msg.data = calculated_error
            self.error_pub.publish(error_msg)
            
            # 5. Publish the Letter String Identification
            letter_msg = String()
            letter_msg.data = detected_letter
            self.letter_pub.publish(letter_msg)
            
            # Debug logs to watch the values live in terminal
            self.get_logger().info(f"CNN Metrics -> Line Error: {calculated_error:.2f} | Letter: {detected_letter}")

        except Exception as e:
            self.get_logger().error(f"Inference loop failure: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    node = CNNProcessorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

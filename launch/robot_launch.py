from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Start the official PS4 Joy Node Driver
        Node(
            package='joy',
            executable='joy_node',
            name='ps4_joy_driver',
            output='screen'
        ),
        
        # 2. Start your Controller Data Node
        Node(
            package='cube_bot',
            executable='controller_data',
            name='controller_logic',
            output='screen'
        ),
        
        # 3. Start your Main Brain Node
        Node(
            package='cube_bot',
            executable='main_program',
            name='main_brain',
            output='screen'
        ),

        Node(
            package='cube_bot',
            executable='image_streamer',
            name='img_streamer',
            output='screen'
        ),

        Node(
            package='cube_bot',
            executable='cnn_processor',
            name='cnn_prcessor',
            output='screen'
        )
     ])

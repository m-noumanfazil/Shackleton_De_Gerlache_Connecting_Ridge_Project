"""Launch Gazebo Fortress with enhanced C1 terrain and spawn lunar_rover.

To launch:
  source /opt/ros/humble/setup.bash
  ros2 launch enhanced/scripts/launch_c1_enh.py
"""

import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    script_dir = Path(__file__).resolve().parent
    enhanced_dir = script_dir.parent
    project_dir = enhanced_dir.parent

    # Rewritten paths pointing to enhanced world and original project files
    world_path = str(enhanced_dir / 'worlds' / 'c1_enh_test.sdf')
    urdf_path = str(project_dir / 'rover_fortress.urdf')

    # Read robot URDF description from original file in project folder
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # 1. Set IGN_GAZEBO_RESOURCE_PATH to include enhanced folder and project folder
    existing_resource_path = os.environ.get('IGN_GAZEBO_RESOURCE_PATH', '')
    res_dirs = f"{enhanced_dir}:{project_dir}"
    if existing_resource_path:
        ign_resource_path = f"{res_dirs}:{existing_resource_path}"
    else:
        ign_resource_path = res_dirs

    set_env = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=ign_resource_path
    )

    # 2. Start Gazebo Fortress with the enhanced world
    ign_gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', '--render-engine', 'ogre2', world_path],
        output='screen'
    )

    # 3. robot_state_publisher Node
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': False
        }]
    )

    # 6. Declare launch arguments for spawn position
    declare_x = DeclareLaunchArgument('x', default_value='0.0', description='Spawn X position')
    declare_y = DeclareLaunchArgument('y', default_value='0.0', description='Spawn Y position')
    declare_z = DeclareLaunchArgument('z', default_value='10.8', description='Spawn Z position')

    # 4. Spawn lunar_rover using ros_gz_sim create executable
    spawn_rover = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-world', 'c1_enh_test',
            '-name', 'lunar_rover',
            '-topic', 'robot_description',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
        ]
    )

    spawn_timer = TimerAction(
        period=5.0,
        actions=[spawn_rover]
    )

    # 5. Parameter bridge node between ROS 2 and Gazebo Fortress
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ]
    )

    return LaunchDescription([
        set_env,
        ign_gazebo,
        robot_state_publisher,
        declare_x,
        declare_y,
        declare_z,
        spawn_timer,
        bridge,
    ])

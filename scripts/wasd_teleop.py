#!/usr/bin/env python3
"""WASD teleoperation node for lunar_rover in ROS 2."""

import select
import sys
import termios
import time
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

LINEAR_SPEED = 0.5
ANGULAR_SPEED = 0.8
HOLD_TIMEOUT = 0.6


class WASDTeleop(Node):
    def __init__(self):
        super().__init__('wasd_teleop')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.linear_speed = LINEAR_SPEED
        self.angular_speed = ANGULAR_SPEED
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.last_key_time = 0.0
        self.stopped = True

    def run(self):
        settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdout.write("WASD Teleop: w/s=drive, a/d=turn, SPACE=stop, q/e=speed -/+ 0.1, Ctrl+C=exit\r\n")
            sys.stdout.flush()

            while rclpy.ok():
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                now = time.time()
                if rlist:
                    key = sys.stdin.read(1)
                    if key == 'w':
                        self.linear_x = self.linear_speed
                        self.angular_z = 0.0
                        self.last_key_time = now
                        self.stopped = False
                    elif key == 's':
                        self.linear_x = -self.linear_speed
                        self.angular_z = 0.0
                        self.last_key_time = now
                        self.stopped = False
                    elif key == 'a':
                        self.linear_x = 0.0
                        self.angular_z = self.angular_speed
                        self.last_key_time = now
                        self.stopped = False
                    elif key == 'd':
                        self.linear_x = 0.0
                        self.angular_z = -self.angular_speed
                        self.last_key_time = now
                        self.stopped = False
                    elif key == ' ':
                        self.linear_x = 0.0
                        self.angular_z = 0.0
                        self.last_key_time = 0.0
                        if not self.stopped:
                            self.publisher_.publish(Twist())
                            self.stopped = True
                    elif key == 'q':
                        self.linear_speed = max(0.1, round(self.linear_speed - 0.1, 2))
                        self.angular_speed = max(0.1, round(self.angular_speed - 0.1, 2))
                        if not self.stopped:
                            if self.linear_x > 0:
                                self.linear_x = self.linear_speed
                            elif self.linear_x < 0:
                                self.linear_x = -self.linear_speed
                            if self.angular_z > 0:
                                self.angular_z = self.angular_speed
                            elif self.angular_z < 0:
                                self.angular_z = -self.angular_speed
                    elif key == 'e':
                        self.linear_speed = round(self.linear_speed + 0.1, 2)
                        self.angular_speed = round(self.angular_speed + 0.1, 2)
                        if not self.stopped:
                            if self.linear_x > 0:
                                self.linear_x = self.linear_speed
                            elif self.linear_x < 0:
                                self.linear_x = -self.linear_speed
                            if self.angular_z > 0:
                                self.angular_z = self.angular_speed
                            elif self.angular_z < 0:
                                self.angular_z = -self.angular_speed
                    elif key == '\x03':
                        break

                if not self.stopped:
                    if (time.time() - self.last_key_time) > HOLD_TIMEOUT:
                        self.linear_x = 0.0
                        self.angular_z = 0.0
                        self.publisher_.publish(Twist())
                        self.stopped = True
                    else:
                        twist = Twist()
                        twist.linear.x = self.linear_x
                        twist.angular.z = self.angular_z
                        self.publisher_.publish(twist)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
            self.publisher_.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    teleop = WASDTeleop()
    try:
        teleop.run()
    except KeyboardInterrupt:
        pass
    finally:
        teleop.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

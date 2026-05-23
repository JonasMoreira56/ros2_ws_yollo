import select
import sys
import termios
import time
import tty

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


HELP_TEXT = """
Controle do P3-AT pelo teclado
------------------------------
Movimento:
   ↑: frente
   ↓: re
   ←: girar para esquerda
   →: girar para direita

Cada clique envia um pulso de velocidade em /cmd_vel.

CTRL-C para sair
"""

MOVE_BINDINGS = {
    '\x1b[A': (1.0, 0.0),
    '\x1b[B': (-1.0, 0.0),
    '\x1b[D': (0.0, 1.0),
    '\x1b[C': (0.0, -1.0),
    '\x1bOA': (1.0, 0.0),
    '\x1bOB': (-1.0, 0.0),
    '\x1bOD': (0.0, 1.0),
    '\x1bOC': (0.0, -1.0),
}


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('p3at_keyboard_teleop')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        self.speed = self.declare_parameter('speed', 0.35).value
        self.turn = self.declare_parameter('turn', 0.75).value
        repeat_rate = self.declare_parameter('repeat_rate', 10.0).value
        self.pulse_duration = self.declare_parameter('pulse_duration', 0.25).value
        self.timeout = 1.0 / repeat_rate

        self.linear = 0.0
        self.angular = 0.0

    def set_motion(self, linear_direction, angular_direction):
        self.linear = linear_direction * self.speed
        self.angular = angular_direction * self.turn

    def stop(self):
        self.linear = 0.0
        self.angular = 0.0

    def publish_motion(self):
        message = Twist()
        message.linear.x = self.linear
        message.angular.z = self.angular
        self.publisher.publish(message)

    def publish_motion_pulse(self, linear_direction, angular_direction):
        self.set_motion(linear_direction, angular_direction)
        self.publish_motion()
        time.sleep(self.pulse_duration)
        self.stop()
        self.publish_motion()


def read_key(tty_file, timeout):
    readable, _, _ = select.select([tty_file], [], [], timeout)
    if not readable:
        return None

    key = tty_file.read(1)
    if key != '\x1b':
        return key

    sequence = key
    while True:
        readable, _, _ = select.select([tty_file], [], [], 0.01)
        if not readable:
            return sequence

        sequence += tty_file.read(1)
        if sequence in MOVE_BINDINGS:
            return sequence

        if len(sequence) >= 3:
            return sequence


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleop()

    try:
        with open('/dev/tty', 'r') as tty_file:
            settings = termios.tcgetattr(tty_file)
            tty.setraw(tty_file.fileno())

            print(HELP_TEXT)
            print(f'velocidade linear: {node.speed:.2f} m/s | angular: {node.turn:.2f} rad/s')

            try:
                while rclpy.ok():
                    key = read_key(tty_file, node.timeout)

                    if key in MOVE_BINDINGS:
                        node.publish_motion_pulse(*MOVE_BINDINGS[key])
                    elif key == '\x03':
                        break
                    elif key is not None:
                        node.stop()
                        node.publish_motion()

                    rclpy.spin_once(node, timeout_sec=0.0)
            finally:
                node.stop()
                node.publish_motion()
                termios.tcsetattr(tty_file, termios.TCSADRAIN, settings)
    except OSError:
        node.get_logger().error(
            'Nao foi possivel acessar /dev/tty. Rode este teleop em um terminal interativo.'
        )
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(main())

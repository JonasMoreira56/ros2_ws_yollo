import select
import sys
import termios
import tty

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


HELP_TEXT = """
Controle do P3-AT pelo teclado
------------------------------
Movimento:
   u    i    o
   j    k    l
   m    ,    .

i: frente        ,: re
j/l: girar       k/espaco: parar
u/o/m/.: curvas

Velocidade:
q/z: aumenta/diminui linear e angular
w/x: aumenta/diminui linear
e/c: aumenta/diminui angular

CTRL-C para sair
"""

MOVE_BINDINGS = {
    'i': (1.0, 0.0),
    ',': (-1.0, 0.0),
    'j': (0.0, 1.0),
    'l': (0.0, -1.0),
    'u': (1.0, 1.0),
    'o': (1.0, -1.0),
    'm': (-1.0, -1.0),
    '.': (-1.0, 1.0),
}

SPEED_BINDINGS = {
    'q': (1.1, 1.1),
    'z': (0.9, 0.9),
    'w': (1.1, 1.0),
    'x': (0.9, 1.0),
    'e': (1.0, 1.1),
    'c': (1.0, 0.9),
}

STOP_KEYS = {'k', ' ', '\r', '\n'}


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('p3at_keyboard_teleop')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        self.speed = self.declare_parameter('speed', 0.35).value
        self.turn = self.declare_parameter('turn', 0.75).value
        repeat_rate = self.declare_parameter('repeat_rate', 10.0).value
        self.timeout = 1.0 / repeat_rate

        self.linear = 0.0
        self.angular = 0.0

    def set_motion(self, linear_direction, angular_direction):
        self.linear = linear_direction * self.speed
        self.angular = angular_direction * self.turn

    def stop(self):
        self.linear = 0.0
        self.angular = 0.0
        self.publish_motion()

    def update_speed(self, speed_scale, turn_scale):
        self.speed *= speed_scale
        self.turn *= turn_scale
        print(f'velocidade linear: {self.speed:.2f} m/s | angular: {self.turn:.2f} rad/s')

    def publish_motion(self):
        message = Twist()
        message.linear.x = self.linear
        message.angular.z = self.angular
        self.publisher.publish(message)


def read_key(tty_file, timeout):
    readable, _, _ = select.select([tty_file], [], [], timeout)
    if not readable:
        return None
    return tty_file.read(1)


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
                        node.set_motion(*MOVE_BINDINGS[key])
                    elif key in SPEED_BINDINGS:
                        node.update_speed(*SPEED_BINDINGS[key])
                    elif key in STOP_KEYS:
                        node.stop()
                    elif key == '\x03':
                        break
                    elif key is not None:
                        node.stop()

                    node.publish_motion()
                    rclpy.spin_once(node, timeout_sec=0.0)
            finally:
                node.stop()
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

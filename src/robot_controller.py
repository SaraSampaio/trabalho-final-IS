# ARQUIVOS USADOS COMO BASE:
# Quase tudo relacionado ao robô: https://github.com/projeto-videomonitoramento/is-wire-RPC/blob/main/exemplo/rpc_server_controle_robot.py
# Leitura do JSON: https://github.com/labviros/is-broker-events/blob/master/src/is_broker_events/service.py (não entendi a parte do argparse)
#                  https://github.com/viniciusbaltoe/is-ros-pkg/blob/main/is_ros_pkg/examples/client.py (fiz como ele, jogando direto o caminho do arquivo)
# Uso do Struct: https://github.com/labviros/is-wire-py 

from is_wire.rpc import ServiceProvider
from is_wire.core import Channel, StatusCode, Status, Logger
from google.protobuf.empty_pb2 import Empty
from google.protobuf.struct_pb2 import Struct
from is_msgs.robot_pb2 import RobotTaskRequest
from is_msgs.common_pb2 import Position
import json
import time

log = Logger(name="robot_controller") 

# Read the configuration file (config.json)
config_file = '../etc/conf/config.json'
with open(config_file) as f:
    config = json.load(f)
    log.info("{}", config)

class Robot():
    def __init__(self, id, x, y, z):
        self.id = id
        self.pos_x = x
        self.pos_y = y
        self.pos_z = z

    def get_id(self):
        return self.id

    def set_position(self, x, y, z):
        self.pos_x = x
        self.pos_y = y
        self.pos_z = z

    def get_position(self):
        return self.pos_x, self.pos_y, self.pos_z

def get_position(struct, ctx):
    log.info("GET POSITION request received...")
    robot_data = RobotTaskRequest()
    robot_data.id = int(struct.fields["id"].number_value)
    for robot in robots_list:
        if robot.id == robot_data.id:
            log.info("Robot found...")
            robot_data.basic_move_task.positions.extend([Position(x = 0, y = 0, z = 0)])
            robot_data.basic_move_task.positions[0].x, robot_data.basic_move_task.positions[0].y, robot_data.basic_move_task.positions[0].z = robot.get_position()
    return robot_data

def set_position(robot_data, ctx):
    time.sleep(0.3)
    log.info("SET POSITION request received...")
    log.info("Validating arguments...")
    if (robot_data.basic_move_task.positions[0].x < 0 or robot_data.basic_move_task.positions[0].y < 0 or robot_data.basic_move_task.positions[0].z < 0):
        return Status(StatusCode.OUT_OF_RANGE, "ALl the 3 dimensions must be positive")
    elif (robot_data.basic_move_task.positions[0].x >5 or robot_data.basic_move_task.positions[0].y > 5 or robot_data.basic_move_task.positions[0].z > 5):
        return Status(StatusCode.OUT_OF_RANGE, "ALl the 3 dimensions must compatible with LabVisio dimensions")
    for robot in robots_list:
        if robot.id == robot_data.id:
            set_x_position = robot_data.basic_move_task.positions[0].x
            set_y_position = robot_data.basic_move_task.positions[0].y
            set_z_position = robot_data.basic_move_task.positions[0].z
            robot.set_position(x=set_x_position, y=set_y_position, z=set_z_position)
            return Status(StatusCode.OK, why = "Movement is OK")


# Robots list - Copied initial coordinates from Wagner's video
log.info("Initializing robots...")
robots_list = [Robot(id=1, x=1, y=2, z=1), Robot(id=2, x=2, y=4, z=1), Robot(id=3, x=6, y=2, z=1), Robot(id=4, x=4, y=1, z=1), Robot(id=5, x=5, y=2, z=1)]

log.info("Creating channel...")
channel = Channel(config["broker_uri"])
provider = ServiceProvider(channel)


# Type of messages must be sent (request and reply)
provider.delegate(
    topic=config["topic_to_get_position"],
    function=config["find_robot_function_name"],
    request_type=Struct,
    reply_type=RobotTaskRequest) 

provider.delegate(
    topic=config["topic_to_set_position"],
    function=config["move_robot_function_name"],
    request_type=RobotTaskRequest,
    reply_type=Empty)

provider.run()
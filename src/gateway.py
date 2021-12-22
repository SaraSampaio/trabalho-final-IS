# ARQUIVOS USADOS COMO BASE:
# Pub/Sub: https://github.com/projeto-videomonitoramento/is_wire1
# Try/Except: https://github.com/projeto-videomonitoramento/is-wire-RPC/blob/main/exemplo/set_position.py
# Unpack: https://github.com/projeto-videomonitoramento/is-wire-RPC/blob/main/exemplo/get_position.py
# Leitura do JSON: https://github.com/labviros/is-broker-events/blob/master/src/is_broker_events/service.py (não entendi a parte do argparse)
#                  https://github.com/viniciusbaltoe/is-ros-pkg/blob/main/is_ros_pkg/examples/client.py (fiz como ele, jogando direto o caminho do arquivo)

from is_wire.core import Channel, Subscription, Message, StatusCode, Status, Logger
from is_wire.rpc import ServiceProvider, LogInterceptor
from is_msgs.common_pb2 import Phrase, Position
from conf.RequisicaoRobo_pb2 import RequisicaoRobo
from is_msgs.robot_pb2 import RobotTaskRequest
from google.protobuf.struct_pb2 import Struct
from google.protobuf.empty_pb2 import Empty
from random import randint
import time
import socket
import json

from is_msgs.robot_pb2 import PathRequest

log = Logger(name="gateway")

# Read the configuration file (config.json)
config_file = '../etc/conf/config.json'
with open(config_file) as f:
    config = json.load(f)
    log.info("{}", config)

def robot_control(requisicaoRobo, ctx):
    time.sleep(0.3)

    if requisicaoRobo.function == config["move_robot_function_name"]:
        log.info("SET POSITION request received from OPERATOR...")
        robot_data = RobotTaskRequest()
        robot_data.id = requisicaoRobo.id
        robot_data.basic_move_task.positions.extend([Position(x = requisicaoRobo.positions.x, y = requisicaoRobo.positions.y, z = requisicaoRobo.positions.z)])

        # Connect to the broker
        log.info("Creating channel...")
        channel = Channel(config["broker_uri"])
        subscription = Subscription(channel)
        request = Message(content=robot_data, reply_to=subscription)
        log.info("Sending SET POSITION request to ROBOT CONTROLLER...")
        channel.publish(request, topic=config["topic_to_set_position"])
        log.info("Waiting SET POSITION reply from ROBOT CONTROLLER...")

        try:
            reply = channel.consume(timeout=1.0)
            log.info("Returning the result back to the user")

        except socket.timeout:
            log.info('No reply :(')
    
        return Status(reply.status.code, why = reply.status.why)
    

    elif requisicaoRobo.function == config["find_robot_function_name"]:
        log.info("GET POSITION request received from OPERATOR...")
        struct = Struct()
        struct.fields["id"].number_value = requisicaoRobo.id

        # Connect to the broker
        log.info("Creating channel...")
        channel = Channel(config["broker_uri"])
        subscription = Subscription(channel)
        request = Message(content=struct, reply_to=subscription)
        log.info("Sending GET POSITION request to ROBOT CONTROLLER...")
        channel.publish(request, topic=config["topic_to_get_position"])
        log.info("Waiting GET POSITION reply from ROBOT CONTROLLER...")

        try:
            reply = channel.consume(timeout=1.0)
            log.info("Returning the result back to the user")
            robot_data = reply.unpack(RobotTaskRequest)
            requisicaoRobo.positions.x = robot_data.basic_move_task.positions[0].x
            requisicaoRobo.positions.y = robot_data.basic_move_task.positions[0].y
            requisicaoRobo.positions.z = robot_data.basic_move_task.positions[0].z
            return requisicaoRobo
      
        except socket.timeout:
            log.info('No reply :(')

while True:
    # Connect to the broker
    log.info("Creating channel...")
    channel = Channel(config["broker_uri"])
    subscription = Subscription(channel)
    subscription.subscribe(topic=config["topic_to_turn_on_system"])
    log.info("Waiting TURN ON message...")

    number = randint(0,100)
    if number >= 50:
        log.info("Successful conection.")
        message_ON = "System ONLINE"
        log.info(message_ON)
        message = Message()
        message.body = message_ON.encode('utf-8')
        channel.publish(message, topic=config["topic_to_turn_on_system"])
        break
    else:
        log.warn("Failed to bring the system online.")
        message_OFF = "Process failed due to an internal error."
        log.info(message_OFF)
        message = Message()
        message.body = message_OFF.encode('utf-8')
        channel.publish(message, topic=config["topic_to_turn_on_system"])


channel = Channel(config["broker_uri"])
provider = ServiceProvider(channel)
logging = LogInterceptor()  # Log requests to console
provider.add_interceptor(logging)

provider.delegate(
    topic="Requisicao.Robo",
    function=robot_control,
    request_type=RequisicaoRobo,
    reply_type=RequisicaoRobo)

log.info("Provider is running and waiting for messages...")
provider.run()
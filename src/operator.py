# ARQUIVOS USADOS COMO BASE:
# Pub/Sub: https://github.com/projeto-videomonitoramento/is_wire1
# Try/Except: https://github.com/projeto-videomonitoramento/is-wire-RPC/blob/main/exemplo/set_position.py
# Unpack: https://github.com/projeto-videomonitoramento/is-wire-RPC/blob/main/exemplo/get_position.py
# Leitura do JSON: https://github.com/labviros/is-broker-events/blob/master/src/is_broker_events/service.py (não entendi a parte do argparse)
#                  https://github.com/viniciusbaltoe/is-ros-pkg/blob/main/is_ros_pkg/examples/client.py (fiz como ele, jogando direto o caminho do arquivo)


from is_wire.core import Channel, Subscription, Message, StatusCode, Logger
from conf.RequisicaoRobo_pb2 import RequisicaoRobo
from google.protobuf.empty_pb2 import Empty
from random import randint
import time
import socket
import json

log = Logger(name="operator")

# Read the configuration file (config.json)
config_file = '../etc/conf/config.json'
with open(config_file) as f:
    config = json.load(f)
    log.info("{}", config)


while True:
    # Connect to the broker
    log.info("Creating channel...")
    channel = Channel(config["broker_uri"])

    # Send a simple text message to turn on the system
    log.info("Creating TURN ON message...")
    message = Message()
    message.body = config["message_to_turn_on_system"].encode('utf-8')
    log.info("Sending TURN ON message...")
    channel.publish(message, topic=config["topic_to_turn_on_system"])

    # Wait for a positive response
    subscription = Subscription(channel)
    subscription.subscribe(topic=config["topic_to_turn_on_system"])
    log.info("Waiting reply...")
    reply = channel.consume()
    reply.body.decode('utf-8')

    if reply.body.decode('utf-8') == "System ONLINE":
        log.info("System ONLINE")
        break
    else:
        log.info("System offline. Trying again...")
        time.sleep(3)

while True:
    time.sleep(1)
    robot_request = RequisicaoRobo()
    robot_request.id = randint(1,5) # There are 5 robots

    robot_request.function = config["move_robot_function_name"] if randint(0,1) == 0 else config["find_robot_function_name"]

    if robot_request.function == config["move_robot_function_name"]:  # Verify dimensions of LabVisio. I assumed that it is 5m x 5m x 5m.   
        robot_request.positions.x = randint(0, 5)
        robot_request.positions.y = randint(0, 5)
        robot_request.positions.z = randint(0, 5)
        log.info(f'Creating SET POSITION request to robot {robot_request.id} with X:{robot_request.positions.x}, Y:{robot_request.positions.y}, Z:{robot_request.positions.z}...')

        # Connect to the broker
        log.info("Creating channel...")
        channel = Channel(config["broker_uri"])
        subscription = Subscription(channel)
        request =  Message(content=robot_request, reply_to=subscription)
        channel.publish(request, topic=config["topic_to_control_the_robot"])
        log.info("Sending SET POSITION request...")
    
        try:
            reply = channel.consume(timeout=1.0)
            log.info("Waiting SET POSITION reply...")

        except socket.timeout:
            log.info('No reply :(')


    elif robot_request.function == config["find_robot_function_name"]:
        log.info("Creating GET POSITION request...")
        empty = Empty()
        request = Message(content=empty, reply_to=subscription)
        channel.publish(request, topic=config["topic_to_control_the_robot"])
        log.info("Sending GET POSITION request...")

        try:
            reply = channel.consume(timeout=1.0)
            log.info("Waiting GET POSITION reply...")
            robot_data = reply.unpack(RequisicaoRobo)
            log.info(f'ROBOT {robot_data.id}: X:{robot_data.positions.x} - Y:{robot_data.positions.y} - Z:{robot_request.positions.z}')

        except socket.timeout:
            print('No reply :(')    
import random
from paho.mqtt import client as mqtt_client
import argparse
import json

parser = argparse.ArgumentParser(
    prog='send.py',
    description="Useage: python send.py '$Server' '$Topic' '$Message' '$Username' '$Password'"
)

parser.add_argument(
    'Server',
    help='Broker server address. Format: String'
)
parser.add_argument(
    'Topic',
    help='Topic to send the message on. Format: String'
)
parser.add_argument(
    'Message',
    help='Message to send. Format: JSON'
)
parser.add_argument(
    'Username',
    help='Username to connect to the broker. Format: String'
)
parser.add_argument(
    'Password',
    help='Password to connect to the broker. Format: String'
)

args = parser.parse_args()

broker = args.Server
topic = args.Topic
message_file = args.Message
username = args.Username
password = args.Password

port = 80

# Read json from the message file
with open(message_file, 'r') as file:
    message = json.load(file)

message = json.dumps(message)

# Generate random client ID so no conflicts with other clients
client_id = f"galaxy-tool-sender-{random.randint(0, 999999)}"


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with reason code: " + str(reason_code))


def connect_mqtt():
    client = mqtt_client.Client(
        client_id=client_id,
        transport="websockets",
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set(username, password)
    client.ws_set_options(path="/ws")
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, topic, message):
    client.loop_start()
    infot = client.publish(topic, message, qos=1)
    infot.wait_for_publish()
    status = infot[0]
    client.loop_stop()
    return status


def send(topic, message):
    client = connect_mqtt()
    print(message)
    status = publish(client, topic, message)
    if status == 0:
        print(f"Sent `{message}` to topic `{topic}`")
    else:
        print(f"Failed to send message {message} to topic {topic}")


if __name__ == '__main__':
    send(topic, message)

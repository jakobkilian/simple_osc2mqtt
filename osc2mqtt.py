import argparse
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import paho.mqtt.client as mqtt
import time
from datetime import datetime

# ----- MESSAGE -----    
def on_message(addr, user_arg, *osc_args):
    if len(osc_args) < 1:
        print("Error: OSC message must contain at least one argument: MQTT_topic")
        return
    topic = osc_args[0]
    message = ' '.join(map(str, osc_args[1:])) # everything after the first space will be the MQTT message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # add timestamp for debugging
    current_time_ms = datetime.now().strftime("%f")[:3]
    print(f"[{current_time}:{current_time_ms}] Received message on {addr} with topic {topic} and message {message}")
    mqtt_client.publish(topic, message)

# ----- CONNECT -----
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

# ----- DISCONNECT -----
def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT Broker")

# ----- MAIN -----
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="The IP address of the MQTT broker")
    parser.add_argument("--port", type=int, help="The OSC port")
    args = parser.parse_args()
    osc_port = args.port if args.port else int(input("Enter the OSC port to be used to receive the messages: ")) # only ask if not provided as arg
    mqtt_broker_ip = args.ip if args.ip else input("Enter the IP address of the MQTT broker (always using standard port 1883): ")  # only ask if not provided as arg

    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/osc2mqtt", on_message, "Message") # only look for "/osc2mqtt" messages

    server = osc_server.ThreadingOSCUDPServer(("localhost", osc_port), dispatcher)
    print(f"Serving on {server.server_address}")

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect

    mqtt_client.connect(mqtt_broker_ip, 1883, 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Closing OSC Server and MQTT Client")
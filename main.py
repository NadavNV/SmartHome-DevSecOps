from flask import Flask, jsonify, request
import json
import paho.mqtt.client as mqtt
import json as jsonlib
import threading
import time

# Setting up the MQTT client
broker = "test.mosquitto.org"
mqtt_client = mqtt.Client("FlaskDevicePublisher")
mqtt_client.connect(broker)

# Temporary local json -> stand in for a future database
file_name = r"./devices.json"

with open(file_name, mode="r", encoding="utf-8") as read_file:
    data = json.load(read_file)

# Prints out an output of the received mqtt messages
def print_device_action(device_name, action_payload, prefix=""):
    for key, value in action_payload.items():
        if isinstance(value, dict):
            # Special case: skip printing "parameters" as a word in output
            if key == "parameters":
                print_device_action(device_name, value, prefix=prefix)
            else:
                print_device_action(device_name, value, prefix=f"{prefix}{key} ")
        else:
            print(f"{device_name} {prefix}{key} changed to {value}")

# Receives the published mqtt payloads -> the mqtt subscriber
def on_message(client, userdata, msg):
    print(f"\n📡 MQTT Message Received on {msg.topic}")
    try:
        payload = jsonlib.loads(msg.payload.decode())
        #print(f"Full Action Payload: {payload}")

        # Extract device_id from topic: expected format project/home/<room>/<device_id>/action
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 5:
            device_id = topic_parts[3]
            # Find device name by device_id
            device_name = next((d['name'] for d in data if d['id'] == device_id), device_id)
        else:
            device_name = "Unknown device"

        print_device_action(device_name, payload)

    except Exception as e:
        print(f"Error decoding payload: {e}")

# Launches the mqtt subscriber in an infinite loop on a different thread
def mqtt_subscriber_thread():
    print("MQTT subscriber thread started", flush=True)
    sub_client = mqtt.Client()
    sub_client.on_message = on_message
    sub_client.connect("test.mosquitto.org")
    sub_client.subscribe("project/home/#")
    sub_client.loop_forever()

# Start subscriber in background
threading.Thread(target=mqtt_subscriber_thread, daemon=True).start()

# Validates that the request data contains all the required fields
def validate_device_data(new_device):
    required_fields = ['id', 'type', 'room', 'name', 'status', 'parameters']
    for field in required_fields:
        if field not in new_device:
            return False
    return True


# Checks the validity of the device id
def check_id(device_id):
    for device in data:
        if device_id == device["id"]:
            return True
    return False


app = Flask(__name__)


# Returns a list of device IDs
@app.get("/api/ids")
def device_ids():
    return [device["id"] for device in data]


# Presents a list of all your devices and their configuration
@app.get("/api/devices")
def all_devices():
    return data


# Get data on a specific device by its ID
@app.get("/api/devices/<device_id>")
def get_device(device_id):
    for device in data:
        if device_id == device["id"]:
            return device
    return jsonify({'error': "ID not found"}), 400


# Adds a new device
@app.post("/api/devices")
def add_device():
    new_device = request.json
    if validate_device_data(new_device):
        if check_id(new_device["id"]):
            return jsonify({'error': "ID already exists"}), 400
        data.append(new_device)

        return jsonify({'output': "device added successfully"}), 200
    return jsonify({'error': 'Missing required field'}), 400


# Deletes a device from the device list
@app.delete("/api/devices/<device_id>")
def delete_device(device_id):
    if check_id(device_id):
        for index, device in enumerate(data):
            if device["id"] == device_id:
                index_to_delete = index
        data.pop(index_to_delete)
        return jsonify({"output": "device was deleted from the database"}), 200
    return jsonify({"error": "id not found"}), 404


# Changes a device configuration or adds a new configuration
@app.put("/api/devices/<device_id>")
def update_device(device_id):
    updated_device = request.json
    if device_id != updated_device["id"]:
        return jsonify({'error': "ID mismatch"}), 400
    if validate_device_data(updated_device):
        for i in range(len(data)):
            if device_id == data[i]["id"]:
                data[i] = updated_device
                return jsonify({'output': "Device updated successfully"}), 200
        return jsonify({'error': "Device not found"}), 404
    return jsonify({'error': 'Missing required field'}), 400


# Sends a real time action to one of the devices
@app.post("/api/devices/<device_id>/action")
def rt_action(device_id):
    action = request.json
    for device in data:
        if device["id"] == device_id:
            for key in action:
                if key == "parameters":
                    if isinstance(action["parameters"], dict):
                        for param_key, param_value in action["parameters"].items():
                            if param_key in device["parameters"]:
                                device["parameters"][param_key] = param_value
                            else:
                                return jsonify({'error': f"Invalid parameter: '{param_key}'"}), 400
                    else:
                        return jsonify({'error': "'parameters' must be a dictionary"}), 400
                elif key != "id" and "type" and "room" and "name":
                    if key in device:
                        device[key] = action[key]
                    else:
                        return jsonify({'error': f"Invalid field: '{key}'"}), 400

            # Formats and publishes the mqtt topic and payload -> the mqtt publisher
            room_topic = device['room'].lower().replace(" ", "-")
            topic = f"project/home/{room_topic}/{device['id']}/action"
            payload = jsonlib.dumps(action)
            mqtt_client.publish(topic, payload)

            return jsonify({'output': "Action applied to device and published via MQTT"}), 200
    return jsonify({'error': "Device not found"}), 404


# Adds required headers to the response
@app.after_request
def add_header(response):
    if request.method == 'OPTIONS':
        response.headers['Allow'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'HEAD, DELETE, POST, GET, OPTIONS, PUT, PATCH'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# GET /api/devices: Get a list of all smart devices with their status.
# POST /api/devices: Register a new smart device (requires device_id, type, and location in payload).
# PUT /api/devices/<device_id>: Update a device's configuration or status (e.g., turn on/off).
# DELETE /api/devices/<device_id>: Remove a smart device.
# Real-Time Actions:
# POST /api/devices/<device_id>/action: Send a command to a device (requires action and optional parameters in JSON payload).
# Device Analytics:
# GET /api/devices/analytics: Fetch usage patterns and status trends for devices.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=True, use_reloader=False)

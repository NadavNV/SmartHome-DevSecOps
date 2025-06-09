from flask import Flask, jsonify, request
import json

file_name = r"./devices.json"

with open(file_name, mode="r", encoding="utf-8") as read_file:
    data = json.load(read_file)


# Validates that the request data contains all the required fields
def validate_device_data(new_device):
    required_fields = ['id', 'type', 'name', 'status', 'parameters']
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


# Presents a list of all your devices and their configuration
@app.get("/api/devices")
def all_devices():
    return data


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
                elif key != "id":
                    if key in device:
                        device[key] = action[key]
                    else:
                        return jsonify({'error': f"Invalid field: '{key}'"}), 400
            return jsonify({'output': "Action applied to device"}), 200
    return jsonify({'error': "Device not found"}), 404


# GET /api/devices: Get a list of all smart devices with their status.
# POST /api/devices: Register a new smart device (requires device_id, type, and location in payload).
# PUT /api/devices/<device_id>: Update a device's configuration or status (e.g., turn on/off).
# DELETE /api/devices/<device_id>: Remove a smart device.
# Real-Time Actions:
# POST /api/devices/<device_id>/action: Send a command to a device (requires action and optional parameters in JSON payload).
# Device Analytics:
# GET /api/devices/analytics: Fetch usage patterns and status trends for devices.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=True)

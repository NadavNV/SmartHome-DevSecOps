from flask import Flask, jsonify, request
from flask_cors import CORS
import json
file_name = r"./devices.json"

with open(file_name, mode="r", encoding="utf-8") as read_file:
    data = json.load(read_file)

def validate_device_data(new_device):
    required_fields = ['id', 'type', 'name', 'status', 'parameters']
    for field in required_fields:
        if field not in new_device:
            return False
    return True

def check_id(device_id):
    ids = []
    for device in data["smart_home_devices"]:
        ids.append(device["id"])
    if device_id in ids:
        return True
    return False


app = Flask(__name__)

@app.get("/api/devices")
def all_devices():
    return data

@app.post("/api/devices")
def add_device():
    new_device = request.json
    if validate_device_data(new_device):
        if check_id(new_device["id"]):
            return jsonify({'error': "ID already exists"}), 400
        data["smart_home_devices"].append(new_device)

        return jsonify({'output': "device added successfully"}), 200
    return jsonify({'error': 'Missing required field'}), 400

@app.delete("/api/devices/<device_id>")
def delete_device(device_id):
    if check_id(device_id):
        for index,device in enumerate(data["smart_home_devices"]):
            if device["id"] == device_id:
                index_to_delete = index
        data["smart_home_devices"].pop(index_to_delete)
        return jsonify({"output": "device was deleted from the database"}), 200
    return jsonify({"error": "id not found"}), 400

@app.put("/api/devices/<device_id>")
def update_device(device_id):
    updated_device = request.json
    if device_id != updated_device["id"]:
        return jsonify({'error': "ID mismatch"}), 400
    if validate_device_data(updated_device):
        for i in range(len(data["smart_home_devices"])):
            if device_id == data["smart_home_devices"][i]["id"]:
                data["smart_home_devices"][i] = updated_device
                return jsonify({'output': "Device updated successfully"}), 200
        return jsonify({'error': "Device not found"}), 400
    return jsonify({'error': 'Missing required field'}), 400




#GET /api/devices: Get a list of all smart devices with their status.
# POST /api/devices: Register a new smart device (requires device_id, type, and location in payload).
# PUT /api/devices/<device_id>: Update a device's configuration or status (e.g., turn on/off).
# DELETE /api/devices/<device_id>: Remove a smart device.
# Real-Time Actions:
# POST /api/devices/<device_id>/action: Send a command to a device (requires action and optional parameters in JSON payload).
# Device Analytics:
# GET /api/devices/analytics: Fetch usage patterns and status trends for devices.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=True)
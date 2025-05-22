from flask import Flask, g, render_template, jsonify
import serial
import threading
import time
import math

app = Flask(__name__)
ser = serial.Serial('COM8', 115200, timeout=1)  # Replace COM8 with your port
time.sleep(2)  # Wait for the serial connection to initialize

sensor_data = {
    "temperature": "----",
    "humidity": "----",
    "gas_level": "----",
    "distance": "----",
    "pulse_value": "----",
    "bpm": "----",  # NEW: BPM Data
    "accel_x": "----",
    "accel_y": "----",
    "accel_z": "----",
    "gyro_x": "----",
    "gyro_y": "----",
    "gyro_z": "----"
}

collected_data = {
    "temperature": [],
    "humidity": [],
    "gas_level": [],
    "pulse_value": [],
    "accel_x": [],
    "accel_y": [],
    "accel_z": []
}

def read_serial():
    print("read_serial() function called")  # Debugging print
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='replace').rstrip()
            print(f"Serial data received: {line}")  # Debugging print
            process_data(line)

def process_data(data):
    if not data:
        return

    try:
        key_value = data.split(":", 1)  # Ensure we only split once
        if len(key_value) < 2:
            print(f"Malformed data received: {data}")
            return

        key, value = key_value[0].strip(), key_value[1].strip()

        if "Temp" in key:
            sensor_data["temperature"] = value.replace("C", "").strip()
        elif "Humidity" in key:
            sensor_data["humidity"] = value.replace("%", "").strip()
        elif "Gas Level" in key:
            sensor_data["gas_level"] = value.strip()
        elif "Distance" in key:
            sensor_data["distance"] = value.replace("cm", "").strip()
        elif "Pulse Sensor Value" in key:
            sensor_data["pulse_value"] = value.strip()
        elif "BPM" in key:  # NEW: Handling BPM
            sensor_data["bpm"] = value.strip()
        elif "Accel X" in key:
            sensor_data["accel_x"] = value.strip()
        elif "Accel Y" in key:
            sensor_data["accel_y"] = value.strip()
        elif "Accel Z" in key:
            sensor_data["accel_z"] = value.strip()
        elif "Gyro X" in key:
            sensor_data["gyro_x"] = value.strip()
        elif "Gyro Y" in key:
            sensor_data["gyro_y"] = value.strip()
        elif "Gyro Z" in key:
            sensor_data["gyro_z"] = value.strip()
        else:
            print(f"Unknown data: {data}")

        print(f"Sensor data updated: {sensor_data}")
        
        # Add data to collected_data for analysis
        add_sensor_data("temperature", sensor_data["temperature"])
        add_sensor_data("humidity", sensor_data["humidity"])
        add_sensor_data("gas_level", sensor_data["gas_level"])
        add_sensor_data("pulse_value", sensor_data["pulse_value"])
        add_sensor_data("accel_x", sensor_data["accel_x"])
        add_sensor_data("accel_y", sensor_data["accel_y"])
        add_sensor_data("accel_z", sensor_data["accel_z"])

    except Exception as e:
        print(f"Error processing data: {e}")
        print(f"Data that caused error: {data}")

# Function to add sensor data (value and timestamp)
def add_sensor_data(sensor_type, value):
    try:
        value = float(value) if value != "----" else 0  # Convert to float or set to 0 if not available
    except ValueError:
        value = 0  # In case of any conversion error, set to 0
    timestamp = time.time()  # Current timestamp in seconds
    collected_data[sensor_type].append((value, timestamp))

# Function to clean up old data (older than 10 seconds)
def cleanup_old_data():
    current_time = time.time()
    for sensor_type in collected_data:
        collected_data[sensor_type] = [
            (value, timestamp) for value, timestamp in collected_data[sensor_type]
            if current_time - timestamp <= 10  # Keep only data from the last 10 seconds
        ]

# Perform analysis on the collected data (e.g., average, etc.)
def analyze_data():
    cleanup_old_data()  # Clean up data older than 10 seconds

    # Calculate averages for the last 10 seconds
    analysis_results = {
        "temperature": sum(value for value, _ in collected_data["temperature"]) / len(collected_data["temperature"]) if collected_data["temperature"] else 0,
        "humidity": sum(value for value, _ in collected_data["humidity"]) / len(collected_data["humidity"]) if collected_data["humidity"] else 0,
        "gas_level": sum(value for value, _ in collected_data["gas_level"]) / len(collected_data["gas_level"]) if collected_data["gas_level"] else 0,
        "pulse_value": sum(value for value, _ in collected_data["pulse_value"]) / len(collected_data["pulse_value"]) if collected_data["pulse_value"] else 0,
        "status": "Normal",  # Default status is "Normal"
    }

    if analysis_results["temperature"] > 40:
        analysis_results["status"] = "High Temperature"
    elif analysis_results["humidity"] > 80:
        analysis_results["status"] = "High Humidity"
    elif analysis_results["gas_level"] > 3000:
        analysis_results["status"] = "Many Harmful Gases, Evacuate"
    
    return analysis_results

@app.route('/')
def index():
    return render_template('index.html', sensor_data=sensor_data)

@app.route('/data')
def get_data():
    return jsonify(sensor_data)

@app.route('/ai_analysis')
def ai_analysis():
    analysis_result = analyze_data()
    return jsonify(analysis_result)

if __name__ == '__main__':
    thread = threading.Thread(target=read_serial)
    thread.daemon = True
    thread.start()
    app.run(debug=True, use_reloader=False)
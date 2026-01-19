from flask import Flask, render_template_string, request, jsonify
import paho.mqtt.client as mqtt
import datetime
import uuid
from Telbot import Telbot
from menu import Menu
import time
import os

# MQTT setup
MQTT_BROKER = "192.168.3.40"
MQTT_PORT = 1883
MQTT_TOPIC = "irrigation/control"

last_echo = ""  # Store last echo message

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        client.subscribe("irrigation/echo")  # Subscribe to echo topic
        client.subscribe("time/request")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    print("⚠️ Disconnected from MQTT broker (rc:", rc, ")")
    if rc != 0:
        print("🔄 Attempting reconnect...")

def on_log(client, userdata, level, buf):
    print("📜 MQTT log:", buf)

def on_message(client, userdata, msg):
    global last_echo
    print(f"Received message: {msg.payload.decode()} on topic: {msg.topic}")
    if msg.topic == "time/request":
        if msg.payload.decode() == "get_time":
            now = datetime.datetime.now()
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            mqtt_publish("time/response", time_str)
    elif msg.topic == "irrigation/echo":
        last_echo = msg.payload.decode()

client_id = f"flask-controller-{uuid.uuid4()}"


def mqtt_publish(topic, payload):
    if mqtt_client.is_connected():
        result = mqtt_client.publish(topic, payload)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print("❌ Publish failed:", result.rc)
    else:
        print("⚠️ MQTT not connected, message not sent:", payload)


# Flask App
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Irrigation Controller</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .input-group { margin-bottom: 10px; }
        input[type=number] { width: 60px; text-align: center; }
        button { padding: 5px 15px; }
        .container {
            display: flex;
            justify-content: flex-start;
            align-items: flex-start;
            gap: 10px;
        }
        .left {
            flex: 1;
            max-width: 170px;
        }
        .right {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .right form {
            margin: 0;
        }
        #echoField {
            width: 150px;
            padding: 5px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Irrigation Controller</h1>
    <div class="container">
        <div class="left">
            <form id="runForm">
                {% for i in range(1, 9) %}
                    <div class="input-group">
                        <label>Station {{ i }}:</label>
                        <input type="number" name="rt{{ i }}" value="0" min="0" step="1" onfocus="this.select()" inputmode="numeric" pattern="[0-9]*">
                    </div>
                {% endfor %}
                <button type="submit">Run</button>
            </form>
        </div>
        <div class="right">
            <form id="onForm">
                <button type="submit">On</button>
            </form>
            <form id="offForm">
                <button type="submit">Off</button>
            </form>
            <form id="updateForm">
                <button type="submit">update_datetime</button>
            </form>
            <input type="text" id="echoField" value="" readonly>
        </div>
    </div>

<script>
function ajaxSubmit(formId, url) {
    document.getElementById(formId).addEventListener("submit", function(e) {
        e.preventDefault();
        let formData = new FormData(this);
        fetch(url, {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            console.log(formId, data);
        })
        .catch(err => console.error(err));
    });
}

ajaxSubmit("runForm", "{{ url_for('send_run') }}");
ajaxSubmit("onForm", "{{ url_for('send_on') }}");
ajaxSubmit("offForm", "{{ url_for('send_off') }}");
ajaxSubmit("updateForm", "{{ url_for('update_datetime') }}");

// Poll for last echo every 2 seconds
setInterval(() => {
    fetch("{{ url_for('get_last_echo') }}")
    .then(res => res.json())
    .then(data => {
        document.getElementById("echoField").value = data.echo || "";
    });
}, 1000);
</script>

</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/run", methods=["POST"])
def send_run():
    runtimes = [request.form.get(f"rt{i}", "0") for i in range(1, 9)]
    payload = "run " + " ".join(runtimes)
    mqtt_publish(MQTT_TOPIC, payload)
    return jsonify({"status": "ok", "message": "Run command sent"})

@app.route("/on", methods=["POST"])
def send_on():
    mqtt_publish(MQTT_TOPIC, "on")
    return jsonify({"status": "ok", "message": "On command sent"})

@app.route("/off", methods=["POST"])
def send_off():
    mqtt_publish(MQTT_TOPIC, "off")
    return jsonify({"status": "ok", "message": "Off command sent"})

@app.route("/update_datetime", methods=["POST"])
def update_datetime():
    now = datetime.datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    mqtt_publish("time/response", time_str)
    return jsonify({"status": "ok", "message": "Datetime updated"})

@app.route("/last_echo", methods=["GET"])
def get_last_echo():
    return jsonify({"echo": last_echo})

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        mqtt_client = mqtt.Client(client_id=client_id, clean_session=True, protocol=mqtt.MQTTv311)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.on_log = on_log
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=120)
        mqtt_client.loop_start()

        #Telegram setup
        bot = Telbot("1737713996:AAFYrAdPpek5AvrRiaprM9sclEUyd7-CJtg")

        menu = Menu(bot,mqtt_client)
        bot.startPoll(menu.callback)

    app.run(debug=True,use_reloader=False, host="0.0.0.0")


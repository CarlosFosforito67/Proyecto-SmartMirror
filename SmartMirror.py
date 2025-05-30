import network
import time
import dht
from machine import Pin, time_pulse_us
from umqtt.simple import MQTTClient

# === WIFI ===
SSID = "TotaLpLay-E5D1"
PASSWORD = "E5D1B440Pq2uLe6Q "

# === MQTT HiveMQ ===
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
CLIENT_ID = "esp32_smartmirror"

# === Pines ===
sensor_luz = Pin(35, Pin.IN)
sensor_dht = dht.DHT11(Pin(21))
trig = Pin(32, Pin.OUT)
echo = Pin(33, Pin.IN)
rele_foco = Pin(26, Pin.OUT)
rele_foco.value(1)

# === Funciones ===
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("🔌 Conectando a WiFi...", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\n✅ Conectado:", wlan.ifconfig())

def medir_distancia_cm():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duracion = time_pulse_us(echo, 1, 30000)
    return (duracion / 2) / 29.1

# === Iniciar conexión ===
conectar_wifi()
cliente = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
cliente.connect()
print("✅ MQTT conectado")

# === Control de tiempo para DHT11 ===
ultimo_envio_dht = time.ticks_ms()

# === Loop rápido ===
while True:
    try:
        distancia = medir_distancia_cm()
        print(f"📏 Distancia: {distancia:.1f} cm")

        if distancia <= 20:
            luz = sensor_luz.value()
            estado_luz = "Detectada" if luz == 0 else "No detectada"
            cliente.publish("smartmirror/luz", estado_luz)

            if luz == 0:
                print("💡 Hay luz → Encender foco")
                rele_foco.value(0)
            else:
                print("🌑 No hay luz → Apagar foco")
                rele_foco.value(1)

            # Solo mide DHT cada 5 segundos
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, ultimo_envio_dht) >= 5000:
                sensor_dht.measure()
                temp = sensor_dht.temperature()
                hum = sensor_dht.humidity()
                cliente.publish("smartmirror/temperatura", str(temp))
                cliente.publish("smartmirror/humedad", str(hum))
                print(f"🌡 {temp}°C  💧 {hum}%")
                ultimo_envio_dht = ahora

        else:
            print("🚫 Nadie cerca → Apagar foco")
            rele_foco.value(1)

        time.sleep(0.5)  # ✅ MÁS FLUIDO

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(1)

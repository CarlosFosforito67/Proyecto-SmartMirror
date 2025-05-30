# ============================
# Aguilar Bueno Carlos Antonio
# Garcia Mora Maribel
# Aguilera Rangel Andre Mauricio
# Ortiz Perez Pablo Alexis
# ============================

import network        # Módulo para manejar conexiones WiFi
import time           # Módulo para pausas, temporizadores y control de tiempo
import dht            # Módulo para el sensor DHT11 (temperatura y humedad)
from machine import Pin, time_pulse_us  # Control de pines GPIO y medir duración de pulsos
from umqtt.simple import MQTTClient     # Cliente MQTT para enviar datos al broker

# === Configuración de red WiFi ===
SSID = ""                        # Nombre de la red WiFi
PASSWORD = " "                 # Contraseña de la red WiFi

# === Configuración del broker MQTT ===
MQTT_BROKER = "broker.hivemq.com"             # Dirección del broker MQTT público (HiveMQ)
MQTT_PORT = 1883                              # Puerto estándar para MQTT sin TLS
CLIENT_ID = "esp32_smartmirror"               # Identificador único del cliente MQTT

# === Definición de pines ===
sensor_luz = Pin(35, Pin.IN)                  # Sensor de luz conectado al pin 35
sensor_dht = dht.DHT11(Pin(21))               # Sensor DHT11 (temp/humedad) conectado al pin 21
trig = Pin(32, Pin.OUT)                       # Pin de disparo del sensor ultrasónico (HC-SR04)
echo = Pin(33, Pin.IN)                        # Pin de eco del sensor ultrasónico
rele_foco = Pin(26, Pin.OUT)                  # Relé que controla un foco/luz conectado al pin 26
rele_foco.value(1)                            # Apaga el foco inicialmente (estado alto = apagado)

# === Función para conectar a WiFi ===
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)       # Se crea una interfaz WiFi en modo cliente (estación)
    wlan.active(True)                         # Activa la interfaz WiFi
    wlan.connect(SSID, PASSWORD)              # Intenta conectarse a la red
    print("🔌 Conectando a WiFi...", end="")
    while not wlan.isconnected():             # Espera hasta que se conecte
        print(".", end="")
        time.sleep(0.5)
    print("\n✅ Conectado:", wlan.ifconfig()) # Muestra la IP asignada

# === Función para medir distancia en centímetros con el sensor ultrasónico ===
def medir_distancia_cm():
    trig.value(0)                             # Asegura que el pulso comience en bajo
    time.sleep_us(2)                          # Espera 2 microsegundos
    trig.value(1)                             # Envía un pulso de 10 microsegundos
    time.sleep_us(10)
    trig.value(0)
    duracion = time_pulse_us(echo, 1, 30000)  # Mide cuánto tarda el eco en volver (hasta 30 ms)
    return (duracion / 2) / 29.1              # Convierte microsegundos a centímetros

# === Inicia la conexión WiFi y MQTT ===
conectar_wifi()                                           # Se conecta al WiFi
cliente = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)  # Crea el cliente MQTT
cliente.connect()                                         # Conecta al broker MQTT
print("✅ MQTT conectado")                                # Confirma la conexión

# === Control de tiempo para medir DHT11 solo cada 5 segundos ===
ultimo_envio_dht = time.ticks_ms()                       # Guarda el tiempo actual

# === Bucle principal del programa ===
while True:
    try:
        distancia = medir_distancia_cm()                 # Mide la distancia del sensor ultrasónico
        print(f"📏 Distancia: {distancia:.1f} cm")        # Imprime la distancia

        if distancia <= 20:                              # Si alguien está a 20 cm o menos
            luz = sensor_luz.value()                     # Lee el valor del sensor de luz (0 = hay luz)
            estado_luz = "Detectada" if luz == 0 else "No detectada"
            cliente.publish("smartmirror/luz", estado_luz)  # Publica el estado de la luz

            if luz == 0:
                print("💡 Hay luz → Encender foco")
                rele_foco.value(0)                        # Enciende el foco (rele en bajo)
            else:
                print("🌑 No hay luz → Apagar foco")
                rele_foco.value(1)                        # Apaga el foco (rele en alto)

            # Controla que solo se mida temperatura y humedad cada 5 segundos
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, ultimo_envio_dht) >= 5000:
                sensor_dht.measure()                     # Mide con el DHT11
                temp = sensor_dht.temperature()          # Lee la temperatura
                hum = sensor_dht.humidity()              # Lee la humedad
                cliente.publish("smartmirror/temperatura", str(temp))  # Publica temperatura
                cliente.publish("smartmirror/humedad", str(hum))       # Publica humedad
                print(f"🌡 {temp}°C  💧 {hum}%")
                ultimo_envio_dht = ahora                 # Actualiza el tiempo de la última medición

        else:
            print("🚫 Nadie cerca → Apagar foco")
            rele_foco.value(1)                            # Apaga el foco si no hay nadie

        time.sleep(0.5)                                   # Pequeña pausa para estabilidad del loop

    except Exception as e:
        print("⚠️ Error:", e)                             # Muestra cualquier error ocurrido
        time.sleep(1)                                     # Espera antes de intentar de nuevo

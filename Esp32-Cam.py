import network     # Importa el módulo para manejar conexiones WiFi
import time        # Importa el módulo para usar pausas y temporizadores
import socket      # Importa el módulo para crear un servidor TCP
import camera      # Importa el módulo específico para controlar la cámara (en placas como ESP32-CAM)
import machine     # Importa el módulo para controlar hardware (GPIO, etc.)

# --- Configuración de WiFi ---
SSID = ''               # Nombre de la red WiFi a la que se va a conectar
PASSWORD = ''         # Contraseña de esa red WiFi

# --- Configuración del pin GPIO del flash LED ---
flash = machine.Pin(4, machine.Pin.OUT)  # Define el pin GPIO4 como salida, para controlar el flash

# --- Función para conectar el dispositivo a la red WiFi ---
def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)   # Crea una interfaz WiFi en modo estación (cliente)
    wlan.active(True)                     # Activa la interfaz WiFi

    if not wlan.isconnected():            # Si no está conectado todavía
        print('Conectando a red...')
        wlan.connect(ssid, password)      # Inicia la conexión con las credenciales proporcionadas
        while not wlan.isconnected():     # Espera en un bucle hasta que se conecte
            time.sleep(0.5)               # Pausa medio segundo entre intentos

    print('Conectado a', ssid)            # Muestra que ya está conectado
    print('IP:', wlan.ifconfig()[0])      # Muestra la IP asignada por la red
    return wlan.ifconfig()[0]             # Retorna la IP asignada

# --- Función para capturar una foto con flash ---
def capture_with_flash():
    flash.value(1)             # Enciende el flash LED (pone el pin en ALTO)
    time.sleep_ms(100)         # Espera 100 milisegundos para una buena iluminación
    buf = camera.capture()     # Captura una imagen y la guarda en un búfer (formato JPEG)
    flash.value(0)             # Apaga el flash (pone el pin en BAJO)
    return buf                 # Retorna la imagen capturada

# --- Función que inicia un servidor web para responder solicitudes ---
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]   # Obtiene la dirección para escuchar (todas las interfaces, puerto 80)
    s = socket.socket()                               # Crea un socket TCP
    s.bind(addr)                                      # Enlaza el socket a la dirección y puerto especificados
    s.listen(1)                                       # Empieza a escuchar conexiones (1 cliente a la vez)
    print('Servidor escuchando en', addr)             # Muestra que el servidor está activo

    while True:                                       # Bucle infinito para aceptar múltiples conexiones
        cl, addr = s.accept()                         # Acepta una conexión entrante (cliente)
        print('Cliente conectado desde', addr)        # Muestra la IP del cliente conectado
        req = cl.recv(1024)                           # Recibe los datos del cliente (hasta 1024 bytes)
        req_str = req.decode('utf-8')                 # Convierte los bytes recibidos en una cadena

        if '/capture' in req_str:                     # Si la solicitud es para capturar imagen
            buf = capture_with_flash()                # Captura una imagen con flash
            response = b'HTTP/1.0 200 OK\r\nContent-Type: image/jpeg\r\n\r\n' + buf
            # Prepara una respuesta HTTP con la imagen capturada
        else:
            response = b'HTTP/1.0 404 NOT FOUND\r\n\r\nRuta no encontrada.'
            # Si no se pidió "/capture", responde con error 404

        cl.send(response)                             # Envía la respuesta al cliente
        cl.close()                                     # Cierra la conexión con el cliente

# --- Función principal que coordina todo ---
def main():
    conectar_wifi(SSID, PASSWORD)                 # Se conecta a la red WiFi especificada
    camera.init(0, format=camera.JPEG)            # Inicializa la cámara en formato JPEG
    start_server()                                # Inicia el servidor para escuchar peticiones

# --- Punto de entrada del programa ---
if __name__ == '__main__':
    main()     # Ejecuta la función principal si este archivo es el programa principal

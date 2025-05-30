import network
import time
import socket
import camera
import machine

# --- Configura tu WiFi ---
SSID = 'Totalplay-E5D1'
PASSWORD = 'E5D1B440Pq2uLe6Q'

# Configurar pin del flash (usualmente GPIO4, ajusta si tu placa es distinta)
flash = machine.Pin(4, machine.Pin.OUT)

def conectar_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando a red...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
    print('Conectado a', ssid)
    print('IP:', wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

def capture_with_flash():
    flash.value(1)         # Enciende el flash
    time.sleep_ms(100)     # Espera para que se ilumine
    buf = camera.capture() # Toma la foto
    flash.value(0)         # Apaga el flash
    return buf

def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Servidor escuchando en', addr)

    while True:
        cl, addr = s.accept()
        print('Cliente conectado desde', addr)
        req = cl.recv(1024)
        req_str = req.decode('utf-8')

        if '/capture' in req_str:
            buf = capture_with_flash()
            response = b'HTTP/1.0 200 OK\r\nContent-Type: image/jpeg\r\n\r\n' + buf
        else:
            response = b'HTTP/1.0 404 NOT FOUND\r\n\r\nRuta no encontrada.'

        cl.send(response)
        cl.close()

def main():
    conectar_wifi(SSID, PASSWORD)
    camera.init(0, format=camera.JPEG)
    start_server()

if __name__ == '__main__':
    main()

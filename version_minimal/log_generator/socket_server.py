import socket
import time
import random

IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.5"]
URLS = ["/", "/login", "/products", "/cart", "/checkout"]
HTTP_CODES = [200, 200, 200, 404, 500, 401, 403]

def generate_log():
    ip = random.choice(IPS)
    url = random.choice(URLS)
    code = random.choice(HTTP_CODES)
    return f'{ip} - - [16/Jun/2025:12:00:00 +0000] "GET {url} HTTP/1.1" {code}'

HOST = "localhost"
PORT = 9999

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"En attente d'une connexion sur {HOST}:{PORT}...")
    conn, addr = s.accept()
    with conn:
        print(f"Connexion acceptée depuis {addr}")
        while True:
            log_line = generate_log() + "\n"
            conn.sendall(log_line.encode())
            time.sleep(1)

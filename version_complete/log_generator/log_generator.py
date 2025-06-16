import socket
import time
import random
import argparse
from datetime import datetime

IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.5"]
URLS = ["/", "/login", "/products", "/cart", "/checkout"]

def parse_args():
    parser = argparse.ArgumentParser(description="Générateur de logs HTTP")
    parser.add_argument("--rate", type=int, default=1, help="Logs par seconde")
    parser.add_argument("--error-rate", type=float, default=0.2, help="Proportion d'erreurs (0.0 à 1.0)")
    parser.add_argument("--error-codes", type=int, nargs="+", default=[404, 500, 401, 403], help="Liste des codes HTTP d'erreur")
    parser.add_argument("--ok-codes", type=int, nargs="+", default=[200], help="Liste des codes HTTP succès")
    parser.add_argument("--error-url-ratio", type=float, default=0.4, help="Ratio d'URLs affectées par les erreurs")
    parser.add_argument("--error-ip-ratio", type=float, default=0.4, help="Ratio d'IPs affectées par les erreurs")
    parser.add_argument("--host", type=str, default="localhost", help="Hôte socket")
    parser.add_argument("--port", type=int, default=9999, help="Port socket")
    return parser.parse_args()

def generate_log(ip, url, code):
    timestamp = datetime.utcnow().strftime('%d/%b/%Y:%H:%M:%S +0000')
    return f'{ip} - - [{timestamp}] "GET {url} HTTP/1.1" {code}'

def main():
    args = parse_args()
    error_ips = random.sample(IPS, max(1, int(len(IPS) * args.error_ip_ratio)))
    error_urls = random.sample(URLS, max(1, int(len(URLS) * args.error_url_ratio)))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((args.host, args.port))
        s.listen(1)
        print(f"Attente de connexion sur {args.host}:{args.port}...")
        conn, addr = s.accept()
        print(f"Connexion acceptée depuis {addr}")

        while True:
            ip = random.choice(IPS)
            url = random.choice(URLS)
            is_error = (ip in error_ips or url in error_urls) and random.random() < args.error_rate
            code = random.choice(args.error_codes if is_error else args.ok_codes)
            log_line = generate_log(ip, url, code) + "\n"
            conn.sendall(log_line.encode())
            time.sleep(1 / args.rate)

if __name__ == "__main__":
    main()

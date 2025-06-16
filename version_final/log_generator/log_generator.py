import socket
import time
import random
import argparse
from kafka import KafkaProducer

# --- Config de base ---
IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.5"]
URLS = ["/", "/login", "/products", "/cart", "/checkout"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=int, default=1, help="Logs par seconde")
    parser.add_argument("--error-rate", type=float, default=0.2)
    parser.add_argument("--error-codes", type=int, nargs="+", default=[404, 500, 401, 403])
    parser.add_argument("--ok-codes", type=int, nargs="+", default=[200])
    parser.add_argument("--error-url-ratio", type=float, default=0.4)
    parser.add_argument("--error-ip-ratio", type=float, default=0.4)
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--mode", choices=["socket", "kafka"], default="socket")
    parser.add_argument("--kafka-topic", type=str, default="http-logs")
    parser.add_argument("--kafka-bootstrap", type=str, default="localhost:9092")
    return parser.parse_args()

def generate_log(ip, url, code):
    return f'{ip} - - [16/Jun/2025:12:00:00 +0000] "GET {url} HTTP/1.1" {code}'

def main():
    args = parse_args()
    rate = args.rate
    delay = 1.0 / rate

    error_ip_set = set(random.sample(IPS, int(len(IPS) * args.error_ip_ratio)))
    error_url_set = set(random.sample(URLS, int(len(URLS) * args.error_url_ratio)))

    if args.mode == "kafka":
        print(f"Connexion à Kafka sur {args.kafka_bootstrap}, topic={args.kafka_topic}")
        producer = KafkaProducer(bootstrap_servers=args.kafka_bootstrap)

    elif args.mode == "socket":
        print(f"En attente de connexion sur {args.host}:{args.port}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((args.host, args.port))
        s.listen(1)
        conn, addr = s.accept()
        print(f"Connexion acceptée depuis {addr}")

    while True:
        ip = random.choice(IPS)
        url = random.choice(URLS)
        is_error = ip in error_ip_set or url in error_url_set
        code_pool = args.error_codes if (is_error and random.random() < args.error_rate) else args.ok_codes
        code = random.choice(code_pool)
        log_line = generate_log(ip, url, code)

        if args.mode == "kafka":
            producer.send(args.kafka_topic, value=log_line.encode('utf-8'))
        elif args.mode == "socket":
            conn.sendall((log_line + "\n").encode('utf-8'))

        print(log_line)
        time.sleep(delay)

if __name__ == "__main__":
    main()

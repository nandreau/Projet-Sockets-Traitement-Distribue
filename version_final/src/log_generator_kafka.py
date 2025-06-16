#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import time
import random
import datetime
from dotenv import load_dotenv
import os
import socket
from kafka import KafkaProducer

# Charger .env
root_env = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, '.env'))
load_dotenv(dotenv_path=root_env)
CLIENT_USERNAME = os.getenv("CLIENT_USERNAME")
CLIENT_PASSWORD = os.getenv("CLIENT_PASSWORD")

# Charger la configuration
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'kafka_config.json')
with open(os.path.abspath(config_path), 'r', encoding='utf-8') as f:
    config = json.load(f)

# Configuration sécurité Kafka (TLS + SASL/PLAIN)
producer = KafkaProducer(
    bootstrap_servers= config["bootstrap_servers"],
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
    sasl_plain_username=CLIENT_USERNAME,
    sasl_plain_password=CLIENT_PASSWORD,
    ssl_cafile=config["ssl_cafile"],
    ssl_check_hostname=False
)

def parse_args():
    """
    Analyse les arguments de la ligne de commande.
    """
    parser = argparse.ArgumentParser(prog="log_generator.py", description="Générateur de logs HTTP (socket ou Kafka)")
    parser.add_argument("--rate", type=float, default=1.0, help="Logs générés par seconde")
    parser.add_argument("--error-rate", type=float, default=0.2, help="Proportion de requêtes erronées pour IP en erreur")
    parser.add_argument("--error-codes", type=int, nargs="+", default=[404,500,401,403], help="Codes HTTP considérés comme erreurs")
    parser.add_argument("--ok-codes", type=int, nargs="+", default=[200], help="Codes HTTP considérés comme réussites")
    parser.add_argument("--error-url-ratio", type=float, default=0.4, help="Fraction d'URLs susceptibles de renvoyer une erreur")
    parser.add_argument("--error-ip-ratio", type=float, default=0.4, help="Fraction d'IP qui génèrent des erreurs")
    parser.add_argument("--host", type=str, default="localhost", help="Hôte cible pour envoi UDP")
    parser.add_argument("--port", type=int, default=9999, help="Port cible pour envoi UDP")
    parser.add_argument("--mode", choices=["socket","kafka"], default="socket", help="Mode de sortie : 'socket' ou 'kafka'")
    return parser.parse_args()


def generate_log_line(ok_codes, error_codes, error_ip_ratio, error_url_ratio):
    """Génère une ligne de log HTTP aléatoire."""
    ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
    method = random.choice(["GET","POST","PUT"])
    paths = ["/","/produit","/panier","/contact","/login","/search"]
    path = random.choice(paths)
    if path == "/produit":
        path += f"/{random.randint(1,1000)}"
    elif path == "/search":
        path += f"?q=chaussette{random.randint(1,100)}"
    if random.random() < error_ip_ratio or random.random() < error_url_ratio:
        status = random.choice(error_codes)
    else:
        status = random.choice(ok_codes)
    size = random.randint(0,5000)
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X)"
    ]
    ua = random.choice(ua_list)
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f"{ip} - - [{timestamp}] \"{method} {path} HTTP/1.1\" {status} {size} \"-\" \"{ua}\""


if __name__ == '__main__':
    args = parse_args()
    if args.mode == 'socket':
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        destination = (args.host, args.port)
        print(f"Mode socket : envoi UDP vers {args.host}:{args.port}...")
    else:
        print(f"Producteur Kafka sécurisé démarré, envoi vers le topic '{config['log_topic']}'...")

    os.makedirs("logs", exist_ok=True)
    try:
        while True:
            line = generate_log_line(
                ok_codes=args.ok_codes,
                error_codes=args.error_codes,
                error_ip_ratio=args.error_ip_ratio,
                error_url_ratio=args.error_url_ratio
            )
            if args.mode == 'kafka':
                producer.send(config['log_topic'], value=line.encode('utf-8'))
            else:
                sock.sendto(line.encode('utf-8'), destination)
            with open("logs/generator.log", "a", encoding='utf-8') as f:
                f.write(line + "\n")
            print(line)
            time.sleep(1.0 / args.rate)
    except KeyboardInterrupt:
        print("\nInterruption manuelle. Générateur arrêté.")

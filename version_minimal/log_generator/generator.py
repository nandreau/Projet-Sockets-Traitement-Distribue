import random
import time

IPS = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.5"]
URLS = ["/", "/login", "/products", "/cart", "/checkout"]
HTTP_CODES = [200, 200, 200, 404, 500, 401, 403]

def generate_log():
    ip = random.choice(IPS)
    url = random.choice(URLS)
    code = random.choice(HTTP_CODES)
    return f'{ip} - - [16/Jun/2025:12:00:00 +0000] "GET {url} HTTP/1.1" {code}'

if __name__ == "__main__":
    while True:
        log = generate_log()
        print(log)
        time.sleep(1)

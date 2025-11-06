import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)

SERVICES = [
    "src/catalog/v1/server.py",
    "src/user/v1/server.py",
    "src/cart/v1/server.py",
    "src/order/v1/server.py",
    "src/notification/v1/server.py",
]

os.environ['PYTHONPATH'] = 'src'

processes = []

for service in SERVICES:
    logging.info(f'Запуск {service}...')
    proc = subprocess.Popen([sys.executable, service])
    processes.append(proc)


logging.info('Все сервисы запущены. Нажмите Ctrl+C для остановки')

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    logging.info('Останавливаем сервисы...')
    for p in processes:
        p.terminate()

    for p in processes:
        p.wait()
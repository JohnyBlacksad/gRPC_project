import sqlite3
import logging
import grpc
from concurrent import futures

from notification.v1.notification_service_pb2 import (
    SendNotificationRequest,
    SendNotificationResponse,
    NotificationType,
)

from notification.v1.notification_service_pb2_grpc import (
    NotificationServiceServicer,
    add_NotificationServiceServicer_to_server,
)

class Database:
    def __init__(self, db_path: str = 'notification.db') -> None:
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         type TEXT NOT NULL,
                         to_addr TEXT NOT NULL,
                         subject TEXT,
                         body TEXT NOT NULL,
                         sent_at INTEGER NOT NULL
                         )
            """)
            conn.commit()

        finally:
            conn.close()

    def log_notification(self, notif_type: str, to_addr: str, subject: str, body: str):
        import time

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute('''
                INSERT INTO notifications (
                         type, to_addr,
                         subject, body,
                         sent_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (notif_type, to_addr, subject, body, int(time.time())))
            conn.commit()

        finally:
            conn.close()


class NotificationService(NotificationServiceServicer):
    def __init__(self, db: Database):
        self.db = db

    def SendNotification(self, request: SendNotificationRequest, context):
        logging.info(f'Отправка уведомления:\n Кому: {request.to}\n Тема: {request.subject}\n Тело: {request.body}')

        self.db.log_notification(
            notif_type=NotificationType.Name(request.type),
            to_addr=request.to,
            subject=request.subject,
            body=request.body
        )

        return SendNotificationResponse(success=True)

def serve():
    db = Database('notification.db')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_NotificationServiceServicer_to_server(NotificationService(db), server)
    server.add_insecure_port('[::]:50055')
    server.start()
    logging.info('Notification Service запущен на порту 50055')
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
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

# The `Database` class in Python initializes a SQLite database connection with a default path for a
# notification database, creates a table for notifications if it does not exist, and provides a method
# to log notification records into the database table.
class Database:
    def __init__(self, db_path: str = 'notification.db') -> None:
        """
        The function initializes a database connection with a default path for a notification database.

        :param db_path: The `db_path` parameter is a string that represents the path to the database
        file. By default, it is set to `'notification.db'`. This parameter is used to initialize the
        database path for the class instance, defaults to notification.db
        :type db_path: str (optional)
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        The function initializes a SQLite database by creating a table for notifications if it does not
        already exist.
        """
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
        """
        The function `log_notification` inserts a notification record into a SQLite database table with
        specified parameters.

        :param notif_type: The `notif_type` parameter in the `log_notification` function represents the
        type or category of the notification being logged. It could be a string indicating the purpose
        or nature of the notification, such as "email", "sms", "alert", "reminder", etc. This parameter
        helps in organizing and
        :type notif_type: str
        :param to_addr: The `to_addr` parameter in the `log_notification` function represents the
        address or destination where the notification will be sent. This could be an email address,
        phone number, username, or any other identifier that specifies the recipient of the notification
        :type to_addr: str
        :param subject: The `subject` parameter in the `log_notification` function refers to the subject
        line of the notification email or message that will be logged in the database. It typically
        contains a brief summary or description of the notification content
        :type subject: str
        :param body: The `body` parameter in the `log_notification` function refers to the content or
        message of the notification that you want to log. This is where you would provide the main
        information or details that you want to include in the notification being stored in the database
        :type body: str
        """

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


# The `NotificationService` class in Python initializes with a database instance and provides a method
# `SendNotification` to log and send notifications.
class NotificationService(NotificationServiceServicer):

    def __init__(self, db: Database):
        """
        The `__init__` function initializes an object with a database instance.

        :param db: Database object that will be used for database operations
        :type db: Database
        """

        self.db = db

    def SendNotification(self, request: SendNotificationRequest, context):

        """
        The function `SendNotification` logs a notification and returns a success response after sending
        the notification.

        :param request: The `SendNotification` method takes in three parameters:
        :type request: SendNotificationRequest
        :param context: The `context` parameter in the `SendNotification` method is typically used to
        provide additional contextual information or configuration settings for the operation being
        performed. It can include details such as the user's session information, security credentials,
        or any other relevant data needed for the operation. In this specific method, the
        :return: The method `SendNotification` is returning a `SendNotificationResponse` object with the
        attribute `success` set to `True`.
        """

        logging.info(f'Отправка уведомления:\n Кому: {request.to}\n Тема: {request.subject}\n Тело: {request.body}')

        self.db.log_notification(
            notif_type=NotificationType.Name(request.type),
            to_addr=request.to,
            subject=request.subject,
            body=request.body
        )

        return SendNotificationResponse(success=True)

def serve():
    """
    The `serve` function sets up a gRPC server for a Notification Service on port 50055.
    """

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
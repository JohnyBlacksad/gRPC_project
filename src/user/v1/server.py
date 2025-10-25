import logging
import sqlite3
import grpc
from concurrent import futures

from user.v1.user_service_pb2 import (
    User,
    CreateUserRequest,
    CreateUserResponse,
    GetUserRequest,
    GetUserResponse,
)

from user.v1.user_service_pb2_grpc import (
    UserServiceServicer,
    add_UserServiceServicer_to_server,
)

class Database:
    def __init__(self, db_path: str = "user.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS user (
                        id TEXT PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        name TEXT,
                        created_at INTEGER NOT NULL
                    )
                """)
            conn.commit()
        finally:
            conn.close()

    def create_user(self, email: str, name: str) -> str:
        import uuid
        import time

        user_id = str(uuid.uuid4())
        created_at = int(time.time())

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute(
                """INSERT INTO users (id, email, name, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, email, name, created_at)
            )
            conn.commit()
            return user_id

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.email" in str(e):
                raise ValueError('Email уже существует')
            raise

        finally:
            conn.close()

    def get_user(self, user_id: str):
        conn = sqlite3.connect(self.db_path)

        try:
            cursor = conn.execute(
                """SELECT id, email, name, created_at FROM users WHERE id = ?""",
                (user_id,)
            )
            return cursor.fetchone()
        finally:
            conn.close()

class UserService(UserServiceServicer):
    def __init__(self, db: Database) -> None:
        self.db = db

    def CreateUser(self, request: CreateUserRequest, context):
        try:
            user_id = self.db.create_user(request.email, request.name or "")

            row = self.db.get_user(user_id)
            user = User(
                id = row[0],
                email=row[1],
                name=row[2] or "",
                created_at=row[3]
                )
            return CreateUserResponse(user=user)

        except ValueError:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, 'Пользователь уже существует')


    def GetUser(self, request: GetUserRequest, context):
        row = self.db.get_user(request.user_id)
        if row is None:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Пользователь не найден')

        user = User(
            id = row[0],
            email= row[1],
            name = row[2],
            created_at= row[3]
        )

        return GetUserResponse(user=user)

def serve():
    db = Database("user.db")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_UserServiceServicer_to_server(UserService(db), server)

    server.add_insecure_port("[::]50051")

    server.start()
    logging.info('User Service запущен на порту 50051')

    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
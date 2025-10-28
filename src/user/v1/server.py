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

# The `Database` class in Python provides methods to initialize a SQLite database, create new user
# records, and retrieve user information based on user ID.
class Database:
    def __init__(self, db_path: str = "user.db"):
        """
        The function initializes a database connection using the specified path or a default path if
        none is provided.

        :param db_path: The `db_path` parameter is a string that represents the path to the database
        file. By default, it is set to "user.db" if no path is provided when initializing the class,
        defaults to user.db
        :type db_path: str (optional)
        """

        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        The `init_db` function creates a SQLite database table for users if it does not already exist.
        """

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
        """
        This Python function creates a new user record in a SQLite database with a unique user ID,
        email, name, and creation timestamp, handling integrity errors related to duplicate emails.

        :param email: The `create_user` function you provided is a method that creates a new user in a
        database table. It generates a unique user ID using `uuid.uuid4()` and a timestamp for the
        creation time. It then inserts the user's information (email, name, user ID, and creation time)
        :type email: str
        :param name: The `name` parameter in the `create_user` function represents the name of the user
        being created. It is a required field and should be a string value. This name will be stored in
        the database along with other user details like email and creation timestamp
        :type name: str
        :return: The `create_user` method returns the `user_id` of the newly created user if the
        insertion into the database is successful. If there is an IntegrityError due to a unique
        constraint violation on the email field, it raises a ValueError with the message 'Email уже
        существует' (Email already exists). If any other type of exception occurs during the database
        operation, it will be raised as is
        """

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
        """
        This Python function retrieves user information from a SQLite database based on the user ID
        provided.

        :param user_id: The `user_id` parameter is a string that represents the unique identifier of a
        user in the database. It is used to retrieve information about a specific user from the `users`
        table based on their ID
        :type user_id: str
        :return: The `get_user` method returns a tuple containing the user's id, email, name, and
        created_at timestamp from the database for the specified user_id.
        """
        conn = sqlite3.connect(self.db_path)

        try:
            cursor = conn.execute(
                """SELECT id, email, name, created_at FROM users WHERE id = ?""",
                (user_id,)
            )
            return cursor.fetchone()
        finally:
            conn.close()


# The `UserService` class in Python defines methods to create and retrieve user information from a
# database using gRPC.
class UserService(UserServiceServicer):
    def __init__(self, db: Database) -> None:
        """
        The function initializes an object with a database parameter.

        :param db: Database object that will be passed to the constructor
        :type db: Database
        """

        self.db = db


    def CreateUser(self, request: CreateUserRequest, context):
        """
        The function `CreateUser` creates a new user in a database and returns the user information in a
        response.

        :param request: The `CreateUser` function takes in three parameters:
        :type request: CreateUserRequest
        :param context: In the provided code snippet, the `context` parameter is used in the `except`
        block to handle an exception. The `context` parameter is likely an instance of the gRPC context
        object that allows you to interact with the gRPC server-side context during the execution of a
        gRPC call
        :return: The `CreateUser` method is returning a `CreateUserResponse` object with the user
        information that was created or retrieved from the database. The user information includes the
        user's ID, email, name, and creation timestamp. If an exception of type `ValueError` is caught
        during the process, the method will abort and return an error message indicating that the user
        already exists.
        """

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
        """
        This Python function retrieves user information from a database and returns it in a response.

        :param request: The `request` parameter in the `GetUser` function is of type `GetUserRequest`.
        It is used to pass the user ID for which the information needs to be retrieved from the database
        :type request: GetUserRequest
        :param context: The `context` parameter in the `GetUser` function is typically used in gRPC
        services to provide contextual information and functionality to the service method. It allows
        you to interact with the gRPC runtime and perform actions such as aborting the RPC call with a
        specific status code and message
        :return: The code snippet is a method named `GetUser` that takes a `GetUserRequest` object and a
        context as parameters. It retrieves a user from the database based on the `user_id` provided in
        the request. If the user is not found in the database, it aborts the operation with a NOT_FOUND
        status and a message 'Пользователь не найден' (User not found
        """

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
    """
    The `serve` function sets up a gRPC server for a User Service and starts it on port 50051.
    """
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
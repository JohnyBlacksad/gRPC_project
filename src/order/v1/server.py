import logging
import sqlite3
import grpc
from concurrent import futures
import time

from order.v1.order_service_pb2 import (
    Order,
    OrderItem,
    CreateOrderRequest,
    CreateOrderResponse,
)

from order.v1.order_service_pb2_grpc import (
    OrderServiceServicer,
    add_OrderServiceServicer_to_server,
)

from catalog.v1.catalog_service_pb2 import GetProductRequest
from catalog.v1.catalog_service_pb2_grpc import CatalogServiceStub

from user.v1.user_service_pb2 import GetUserRequest
from user.v1.user_service_pb2_grpc import UserServiceStub

from cart.v1.cart_service_pb2 import (
    GetCartRequest,
    ClearCartRequset,
)

from cart.v1.cart_service_pb2_grpc import CartServiceStub

from notification.v1.notification_service_pb2 import (
    SendNotificationRequest,
    NotificationType,
)
from notification.v1.notification_service_pb2_grpc import NotificationServiceStub



# The `Database` class in Python initializes a SQLite database connection, creates tables for orders
# and order items, and provides methods to create new orders with associated items.
class Database:
    def __init__(self, db_path: str = 'order.db') -> None:
        """
        This Python function initializes a database connection using a specified path or a default path
        if none is provided.

        :param db_path: The `db_path` parameter is a string that represents the path to the database
        file. By default, it is set to `'order.db'`. This parameter is used to initialize the database
        path for the class instance, defaults to order.db
        :type db_path: str (optional)
        """

        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        The `init_db` function creates two tables, `orders` and `order_item`, in a SQLite database if
        they do not already exist.
        """

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_amount INTEGER NOT NULL,
                    currency_code TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS order_item (
                    order_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    currency_code TEXT NOT NULL,
                    FOREIGN KEY(order_id) REFERENCES orders(id)
                )
                """)
            conn.commit()
        finally:
            conn.close()

    def create_order(self, user_id: str, items, total_amount: int, currency_code: str):

        """
        The function creates a new order in a SQLite database with order details and associated items.

        :param user_id: The `user_id` parameter is a string that represents the unique identifier of the
        user who is placing the order. It is used to associate the order with a specific user in the
        database
        :type user_id: str
        :param items: The `items` parameter in the `create_order` method is expected to be a collection
        of objects representing the individual items in the order. Each item object should have the
        following attributes:
        :param total_amount: The `total_amount` parameter in the `create_order` function represents the
        total amount of the order in the specified currency. It is an integer value that indicates the
        total cost of all items in the order before any discounts or taxes are applied
        :type total_amount: int
        :param currency_code: The `currency_code` parameter in the `create_order` function is a string
        that represents the currency code used for the order. It specifies the currency in which the
        total amount for the order is denominated. For example, "USD" for US Dollars, "EUR" for Euros,
        "JP
        :type currency_code: str
        :return: The `create_order` method returns the `order_id` of the newly created order.
        """

        order_id = f"ord-{int(time.time())}"
        created_at = int(time.time())

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute(
                '''
                INSERT INTO orders (id, user_id, status, total_amount,
                currency_code, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (order_id, user_id, 'CREATED', total_amount, currency_code, created_at)
            )

            for item in items:
                conn.execute(
                    '''
                    INSERT INTO order_items (order_id, product_id,
                    product_name, quantity, price, currency_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (order_id, item.product_id, item.product_name,
                     item.quantity, item.price, item.currency_code)
                )
            conn.commit()
            return order_id

        finally:
            conn.close()

# The `OrderService` class in Python defines methods for creating orders by interacting with gRPC
# services for user, cart, catalog, database, and notifications.
class OrderService(OrderServiceServicer):
    def __init__(self, db: Database):
        """
        The function initializes an object with a database parameter.

        :param db: The parameter `db` in the `__init__` method is of type `Database`. It is used to
        initialize an instance of the class with a database object
        :type db: Database
        """
        self.db = db


    def CreateOrder(self, request: CreateOrderRequest, context):

        """
        The function `CreateOrder` processes a new order by interacting with user, cart, catalog,
        database, and notification services in a gRPC environment.

        :param request: The code you provided seems to be a Python function for creating an order. It
        interacts with gRPC services for user information, cart details, product catalog, and
        notifications. Here's a breakdown of the code:
        :type request: CreateOrderRequest
        :param context: The `context` parameter in the `CreateOrder` function is typically used in gRPC
        services to handle errors and manage the lifecycle of the RPC call. It provides methods for
        aborting the RPC call with a specific status code and message
        :return: The `CreateOrder` function returns a `CreateOrderResponse` object containing the order
        details such as order ID, user ID, order status, items in the order, total amount, currency
        code, and creation timestamp.
        """

        user_id = request.user_id

        user_channel = grpc.insecure_channel('localhost:50052')
        user_stub = UserServiceStub(user_channel)
        user_response = None

        try:
            user_response = user_stub.GetUser(GetUserRequest(user_id=user_id))
        except grpc.RpcError as e:
            context.abort(e.code(), f'Ошибка User Service: {e.details()}')

        user_email = user_response.user.email

        cart_channel = grpc.insecure_channel('localhos:50053')
        cart_stub = CartServiceStub(cart_channel)

        cart_response = None
        try:
            cart_response = cart_stub.GetCart(GetCartRequest(user_id=user_id))
        except grpc.RpcError as e:
            context.abort(e.code(), f'Ошибка Cart Service: {e.details()}')

        if not cart_response.items:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'Корзина пуста')

        catalog_channel = grpc.insecure_channel('localhost:50051')
        catalog_stub = CatalogServiceStub(catalog_channel)
        validated_items = []
        total_amount = 0
        currency_code = 'RUB'

        for item in cart_response.items:
            product_response = None
            try:
                product_response = catalog_stub.GetProduct(GetProductRequest(product_id=item.product_id))
            except grpc.RpcError as e:
                context.abort(e.code(), f'Товар {item.product_id} не найден: {e.details()}')
            product = product_response.product

            if not product.in_stock:
                context.abort(grpc.StatusCode.FAILED_PRECONDITION, f'Товар {product.name} нет в наличии')

            validated_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                price=product.price,
                currency_code=product.currency_code
            )
            validated_items.append(validated_item)
            total_amount+=product.price * item.quantity
            currency_code=product.currency_code

        order_id = self.db.create_order(user_id,
                                        validated_items,
                                        total_amount,
                                        currency_code)

        try:
            cart_stub.ClearCart(ClearCartRequset(user_id=user_id))

        except grpc.RpcError as e:
            logging.warning(f'Не удалось очистить корзину для {user_id}: {e}')

        notification_channel = grpc.insecure_channel('localhost:50055')
        notification_stub = NotificationServiceStub(notification_channel)

        try:
            notification_stub.SendNotification(SendNotificationRequest(
                type=NotificationType.NOTIFICATION_TYPE_EMAIL,
                to=user_email,
                subject='Ваш заказ оформлен!',
                body=f'Спасибо! Номер заказа {order_id}. Сумма: {total_amount // 100}.{total_amount%100:02d} {currency_code}'
            ))

        except grpc.RpcError as e:
            logging.warning(f'Не удалось отправить уведомление: {e}')

        order = Order(
            id=order_id,
            user_id=user_id,
            status=Order.Status.STATUS_CREATED,
            items=validated_items,
            total_amount=total_amount,
            currency_code=currency_code,
            created_at=int(time.time())
        )
        return CreateOrderResponse(order=order)


def serve():

    """
    The `serve` function sets up a gRPC server for an Order Service using a database and starts it on
    port 50054.
    """

    db = Database('order.db')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_OrderServiceServicer_to_server(OrderService(db), server)
    server.add_insecure_port('[::]:10054')
    server.start()
    logging.info('Order Service запущен на порту 10054')
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
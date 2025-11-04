import logging
import sqlite3
import grpc

from concurrent import futures


from cart.v1.cart_service_pb2 import (
    CartItem,
    AddItemRequest,
    AddItemResponse,
    GetCartRequest,
    GetCartResponse,
)

from cart.v1.cart_service_pb2_grpc import (
    CartServiceServicer,
    add_CartServiceServicer_to_server,
)


# The `Database` class in Python provides methods to manage a shopping cart stored in a SQLite
# database, allowing users to add items, retrieve cart contents, and clear the cart based on user IDs.
class Database:
    def __init__(self, db_path: str = "cart.db") -> None:
        """
        This Python function initializes an object with a default database path and initializes the
        database.

        :param db_path: The `db_path` parameter is a string that represents the path to the database
        file. By default, it is set to "cart.db" if no value is provided when initializing the class,
        defaults to cart.db
        :type db_path: str (optional)
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        The `init_db` function creates a SQLite database table for storing cart items with specific
        columns.
        """
        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS cart_items (
                            user_id TEXT NOT NULL,
                            product_id TEXT NOT NULL,
                            product_name TEXT NOT NULL,
                            quantity INTEGER NOT NULL,
                            price INTEGER NOT NULL,
                            currency_code TEXT NOT NULL,
                            PRIMARY KEY (user_id, product_id)
                         )
                         """)
            conn.commit()
        finally:
            conn.close()

    def add_item(self, user_id: str,
                 product_id: str,
                 product_name: str,
                 quantity: int,
                 price: int,
                 currency_code: str):
        """
        This function adds an item to a user's cart in a SQLite database, updating the quantity if the
        item is already in the cart.

        :param user_id: The `user_id` parameter is a string that represents the unique identifier of the
        user who is adding an item to the cart
        :type user_id: str
        :param product_id: The `product_id` parameter is a unique identifier for a specific product in
        the database. It is used to distinguish one product from another and is typically a string or
        integer value that is assigned to each product when it is added to the system
        :type product_id: str
        :param product_name: The `product_name` parameter in the `add_item` method refers to the name of
        the product being added to the cart. It is a string type parameter that should contain the name
        or title of the product that the user is adding to their cart. This information is used to
        display the product name
        :type product_name: str
        :param quantity: The `add_item` method you provided seems to have a small typo in the SQL query.
        The `WHERE` keyword is misspelled as `WERE`. Here is the corrected version:
        :type quantity: int
        :param price: The `price` parameter in the `add_item` method represents the price of the product
        being added to the cart. It is an integer value that indicates the cost of one unit of the
        product in the specified `currency_code`
        :type price: int
        :param currency_code: The `currency_code` parameter in the `add_item` method represents the
        currency code used for the price of the product being added to the cart. It is a string that
        typically follows the ISO 4217 standard for currency codes, such as "USD" for US Dollars or
        "EUR" for
        :type currency_code: str
        """

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                        UPDATE cart_items
                        SET quantity = quantity + ?
                        WERE user_id = ? AND product_id = ?
                         """, (quantity, user_id, product_id))

            if conn.total_changes == 0:
                conn.execute(
                    """
                    INSERT INTO cart_items (
                        user_id, product_id, product_name,
                        quantity, price, currency_code
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, product_id, product_name, quantity, price, currency_code)
                )
                conn.commit()
        finally:
            conn.close()


    def get_cart(self, user_id: str):
        """
        The above Python code defines methods to retrieve and clear a user's shopping cart items from a
        SQLite database based on the user ID.

        :param user_id: The `user_id` parameter is a unique identifier for a user in the system. It is
        used to associate a user with their cart items in the database
        :type user_id: str
        :return: The `get_cart` method is returning a list of tuples containing the product_id,
        product_name, quantity, price, and currency_code for items in the cart belonging to the
        specified user_id. The `clear_cart` method is not returning anything, it is simply deleting all
        cart items for the specified user_id from the database.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                                    SELECT product_id, product_name,
                                    quantity, price, currency_code
                                    FROM cart_items
                                    WHERE user_id = ?
                                    """, (user_id,))
            return cursor.fetchall()

        finally:
            conn.close()

    def clear_cart(self, user_id: str):
        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()


# The `CartService` class in Python defines methods for adding items to a cart and retrieving cart
# details using a database instance.
class CartService(CartServiceServicer):
    def __init__(self, db: Database):
        """
        The `__init__` function initializes an object with a database instance passed as a parameter.

        :param db: The parameter `db` in the `__init__` method is of type `Database`. It is being passed
        to the constructor of the class as an argument
        :type db: Database
        """
        self.db = db

    def AddItem(self, request: AddItemRequest, context):
        """
        The AddItem function adds an item to the database with specified details.

        :param request: The `AddItem` function takes three parameters:
        :type request: AddItemRequest
        :param context: The `context` parameter in the `AddItem` method is typically used in gRPC
        services to provide additional information or context about the request being made. It can
        include details such as metadata, authentication information, or other contextual data that may
        be relevant for processing the request. In this specific method,
        :return: An AddItemResponse object is being returned.
        """
        self.db.add_item(
            user_id=request.user_id,
            product_id=request.product_id,
            product_name='Товар из запроса',
            quantity=request.quantity,
            price=10000,
            currency_code="RUB"
        )

        return AddItemResponse()

    def GetCart(self, request: GetCartRequest, context):
        """
        The function `GetCart` retrieves cart items for a user, calculates the total amount, and returns
        the response with items, total amount, and currency code.

        :param request: The `GetCart` function takes three parameters:
        :type request: GetCartRequest
        :param context: The `GetCart` function takes in three parameters:
        :return: The GetCart method returns a GetCartResponse object containing a list of CartItem
        objects representing the items in the user's cart, the total amount of the cart, and the
        currency code used for the prices.
        """
        rows = self.db.get_cart(request.user_id)
        items = []
        total_amount = 0
        currency_code = "RUB"

        for row in rows:
            product_id, product_name, quantity, price, curr = row
            items.append(
                CartItem(
                    product_id=product_id,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    currency_code=curr
                )
            )
            total_amount += price * quantity
            currency_code = curr

        return GetCartResponse(
            items=items,
            total_amount=total_amount,
            currency_code=currency_code
        )


def serve():
    """
    The `serve` function sets up a gRPC server for a Cart Service using a specified database and port.
    """
    db = Database("cart.db")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_CartServiceServicer_to_server(CartService(db), server)
    server.add_insecure_port("[::]50053")
    server.start()
    logging.info('Cart Service запущен на порту 50053')
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
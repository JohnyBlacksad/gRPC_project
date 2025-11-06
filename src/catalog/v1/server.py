import logging
import sqlite3
import grpc
from concurrent import futures

from catalog.v1.catalog_service_pb2 import (
    Product,
    GetProductRequest,
    GetProductResponse,
    ListProductsRequest,
    ListProductsResponse,
)

from catalog.v1.catalog_service_pb2_grpc import (
    CatalogServiceServicer,
    add_CatalogServiceServicer_to_server,
)

# The `Database` class in Python initializes a SQLite database, creates a products table if it does
# not exist, inserts demo data if the table is empty, and provides a context manager for establishing
# a connection to the database.
class Database:
    def __init__(self, db_path: str = "catalog.db"):
        """
        The function initializes a database connection using a specified path or a default path if none
        is provided.

        Args:
          db_path (str): The `db_path` parameter is a string that represents the path to the database
        file. The default value for `db_path` is "catalog.db" if no value is provided when initializing
        the class. Defaults to catalog.db
        """

        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        The `init_db` function initializes a database by creating a products table if it does not exist
        and inserts demo data if the table is empty.
        """

        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    currency_code TEXT NOT NULL,
                    in_stock BOOLEAN NOT NULL
                    )
            """)
            cursor = conn.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                self._insert_demo_data(conn)

    def _insert_demo_data(self, conn):
        """
        The function `_insert_demo_data` inserts demo product data into a table named `products` in a
        database connection.

        Args:
          conn: The `conn` parameter in the `_insert_demo_data` method is typically a connection object
        to a database. This connection object allows you to interact with the database by executing SQL
        queries and commands. In this case, it is being used to insert demo product data into a table
        named `products`.
        """

        demo_products = [
            ('prod-1', 'Смартфон XYZ', 'Флагманский смартфон', 59900, 'RUB', True),
            ('prod-2', 'Наушники PRO', 'Беспроводные наушники', 12900, 'RUB', True),
            ('prod-3', 'Чехол', 'Силиконовый чехол', 990, 'RUB', False),
        ]
        conn.executemany("""
            INSERT INTO products (id, name, description, price, currency_code, in_stock)
            VALUES (?, ?, ?, ?, ?, ?)
            """, demo_products)
        logging.info('Добавлены демо-товары в таблицу products')

    def get_connection(self):
        """
        The function `get_connection` returns a connection to a SQLite database using the specified
        `db_path`.

        Returns:
          An SQLite database connection is being returned.
        """
        return sqlite3.connect(self.db_path)



# The `CatalogService` class in Python provides methods to retrieve product information from a
# database based on product ID or list all products.
class CatalogService(CatalogServiceServicer):
    def __init__(self, db: Database) -> None:
        """
        The function initializes an object with a database parameter.

        Args:
          db (Database): The parameter `db` in the `__init__` method is of type `Database`. It is used
        to initialize an instance of the class with a database object.
        """
        self.db = db

    def GetProduct(self, request: GetProductRequest, context):
        """
        This Python function retrieves product information from a database based on the provided product
        ID.

        Args:
          request (GetProductRequest): The `GetProduct` function you provided is a method that retrieves
        product information from a database based on the product ID provided in the request. Here's an
        explanation of the parameters used in the function:
          context: In the provided code snippet, the `context` parameter is used in the gRPC service
        method `GetProduct` as an argument. In gRPC, the `context` parameter typically represents the
        context of the RPC call, which includes metadata and other information related to the request
        and response.

        Returns:
          The code snippet is a Python function that retrieves product information from a database based
        on the provided product ID. If the product is found in the database, it constructs a `Product`
        object with the retrieved information and returns a `GetProductResponse` object containing the
        product.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("SELECT id, name, description, price, currency_code, in_stock FROM products WHERE id = ?",
                    (request.product_id,))
            row = cursor.fetchone()

            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, "Товар не найден")

            product = Product(
                id = row[0],
                name = row[1],
                description = row[2],
                price = row[3],
                currency_code = row[4],
                in_stock = bool(row[5])
            )

            return GetProductResponse(product=product)

        finally:
            conn.close()


    def ListProducts(self, request: ListProductsRequest, context):
        """
        The function ListProducts retrieves product information from a database and returns a list of
        Product objects.

        Args:
          request (ListProductsRequest): The `ListProducts` function you provided seems to be a method
        that retrieves a list of products from a database and returns them as a response. The
        `ListProductsRequest` parameter is likely the request object that contains any parameters or
        filters for the product listing.
          context: In the provided code snippet, the `context` parameter is a parameter that is commonly
        used in gRPC service implementations. It represents the context of the current RPC (Remote
        Procedure Call) being handled. The context can contain information such as metadata, deadlines,
        cancellation signals, and other details related to the

        Returns:
          The code snippet is a method called `ListProducts` that takes a request of type
        `ListProductsRequest` and a context parameter.
        """
        conn = self.db.get_connection()

        try:
            cursor = conn.execute(
                "SELECT id, name, description, price, currency_code, in_stock FROM products"
            )
            products = []
            for row in cursor.fetchall():
                products.append(
                    Product(
                        id = row[0],
                        name = row[1],
                        description = row[2],
                        price = row[3],
                        currency_code = row[4],
                        in_stock=bool(row[5])
                    )
                )

            return ListProductsResponse(products=products)

        finally:
            conn.close()


def serve():
    """
    The `serve` function starts a gRPC server for a Catalog Service on port 10051.
    """
    db = Database('catalog.db')

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_CatalogServiceServicer_to_server(CatalogService(db), server)
    server.add_insecure_port("[::]:10051")

    server.start()
    logging.info("Catalog Service запущен на порту 10051")

    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
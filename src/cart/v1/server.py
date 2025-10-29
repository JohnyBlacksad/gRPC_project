import logging
import sqlite3
import grpc

from concurrent import futures
import time

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

class Database:
    def __init__(self, db_path: str = "cart.db") -> None:
        self.db_path = db_path
        self.init_db()

    def init_db(self):
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

class CartService(CartServiceServicer):
    def __init__(self, db: Database):
        self.db = db

    def AddItem(self, request: AddItemRequest, context):
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
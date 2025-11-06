"""Онлайн-магазин: API Gateway

Этот модуль реализует API Gateway для микросервисной архитектуры онлайн-магазина.
Он объединяет gRPC-сервисы (пользователи, каталог, корзина, заказы) и предоставляет
единый RESTful интерфейс через FastAPI.

Сервисы:
- `user`: управление пользователями
- `catalog`: управление товарами
- `cart`: работа с корзиной
- `order`: создание и отслеживание заказов

Все gRPC-соединения устанавливаются через незащищённые каналы (insecure_channel)
на предопределённых портах (например, `localhost:10052` для user-service).

Примечание:
- Вся обработка ошибок gRPC-вызовов преобразуется в HTTP-исключения (HTTPException),
  с сохранением семантики кодов состояния (например, `ALREADY_EXISTS` → 409).
- Используются Pydantic-модели для валидации входных данных и формирования ответов.
"""

import logging
import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from user.v1.user_service_pb2 import CreateUserRequest
from user.v1.user_service_pb2_grpc import UserServiceStub

from catalog.v1.catalog_service_pb2 import ListProductsRequest
from catalog.v1.catalog_service_pb2_grpc import CatalogServiceStub

from cart.v1.cart_service_pb2 import AddItemRequest, GetCartRequest
from cart.v1.cart_service_pb2_grpc import CartServiceStub

from order.v1.order_service_pb2 import CreateOrderRequest
from order.v1.order_service_pb2_grpc import OrderServiceStub


class CreateUserJSON(BaseModel):
    """Модель входных данных для создания пользователя.

    Attributes:
        email (str): Электронная почта пользователя. Обязательное поле.
        name (str | None): Имя пользователя. Необязательное, по умолчанию `None`.
    """

    email: str
    name: str | None = None


class AddCartItemJSON(BaseModel):
    """Модель входных данных для добавления товара в корзину.

    Attributes:
        user_id (str): UUID-идентификатор пользователя.
        product_id (str): UUID-идентификатор товара.
        quantity (int): Количество единиц товара. По умолчанию — 1.
    """

    user_id: str
    product_id: str
    quantity: int = 1


class CreateOrderJSON(BaseModel):
    """Модель входных данных для создания заказа.

    Attributes:
        user_id (str): UUID-идентификатор пользователя.
    """

    user_id: str



class UserResponseJSON(BaseModel):
    """Модель ответа при создании/получении пользователя.

    Attributes:
        id (str): Уникальный UUID-идентификатор пользователя.
        email (str): Электронная почта.
        name (str): Имя (включая значение по умолчанию, если не указано).
        created_at (str): Дата и время создания в ISO 8601 формате (например, `"2025-11-07T12:34:56Z"`).
    """

    id: str
    email: str
    name: str
    created_at: str



class ProductResponseJSON(BaseModel):
    """Модель данных о товаре из каталога.

    Attributes:
        id (str): UUID товара.
        name (str): Наименование.
        description (str): Описание.
        price (int): Цена в *минимальных единицах валюты* (например, копейках).
        currency_code (str): Код валюты по ISO 4217 (например, `"RUB"`).
        in_stock (bool): Доступность на складе.
    """

    id: str
    name: str
    description: str
    price: int
    currency_code: str
    in_stock: bool



class CartItemJSON(BaseModel):
    """Модель элемента корзины — расширенная информация о товаре и количестве.

    Attributes:
        product_id (str): UUID товара.
        product_name (str): Наименование товара (для отображения).
        quantity (int): Количество единиц в корзине.
        price (int): Цена за единицу (в минимальных единицах).
        currency_code (str): Код валюты.
    """

    product_id: str
    product_name: str
    quantity: int
    price: int
    currency_code: str


class CartResponseJSON(BaseModel):
    """Модель полного состояния корзины пользователя.

    Attributes:
        items (List[CartItemJSON]): Список позиций в корзине.
        total_amount (int): Общая сумма (в минимальных единицах валюты).
        currency_code (str): Код валюты корзины (ожидается однородная валюта).
    """

    items: List[CartItemJSON]
    total_amount: int
    currency_code: str


class OrderResponseJSON(BaseModel):
    """Модель созданного заказа.

    Attributes:
        id (str): UUID заказа.
        user_id (str): UUID пользователя.
        status (str): Статус заказа в виде строки (например, `"CREATED"`).
        total_amount (int): Общая сумма заказа.
        currency_code (str): Валюта.
        items (List[CartItemJSON]): Состав заказа (копия позиций из корзины на момент создания).
    """

    id: str
    user_id: str
    status: str
    total_amount: int
    currency_code: str
    items: List[CartItemJSON]


def get_user_stub():
    """Создаёт gRPC-стаб для сервиса управления пользователями.

    Подключается к `user-service` по адресу `localhost:10052` через незащищённый канал.
    Используется для вызова метода `CreateUser`.

    Returns:
        UserServiceStub: gRPC-стаб для взаимодействия с user-service.

    Note:
        В продакшене рекомендуется использовать защищённые каналы (TLS)
        и кеширование/пулы соединений (например, через `grpc.aio` или connection pool).
    """

    return UserServiceStub(grpc.insecure_channel('localhost:10052'))


def get_catalog_stub():
    """Создаёт gRPC-стаб для catalog-service (`localhost:10051`)."""

    return CatalogServiceStub(grpc.insecure_channel('localhost:10051'))


def get_cart_stub():
    """Создаёт gRPC-стаб для cart-service (`localhost:10053`)."""

    return CartServiceStub(grpc.insecure_channel('localhost:10053'))


def get_order_stub():
    """Создаёт gRPC-стаб для order-service (`localhost:10054`)."""

    return OrderServiceStub(grpc.insecure_channel('localhost:10054'))


app = FastAPI(title='Online Shop API Gateway', version='1.0.1')



@app.post('/users', response_model=UserResponseJSON)
def create_user(payload: CreateUserJSON):
    """Создаёт нового пользователя через user-service.

    Отправляет запрос `CreateUser` в gRPC-сервис `user.v1.UserService`.
    Если пользователь с указанным email уже существует — возвращает HTTP 409.

    Args:
        payload (CreateUserJSON): Данные пользователя (email, name).

    Returns:
        UserResponseJSON: Созданный пользователь с `id`, `email`, `name`, `created_at`.

    Raises:
        HTTPException:
            - 409 (Conflict), если email уже занят (`grpc.StatusCode.ALREADY_EXISTS`).
            - 400 (Bad Request) при других ошибках валидации от сервиса.
            - 500 (Internal Server Error), если произошла неожиданная gRPC-ошибка.

    Note:
        Если `name` не передан, используется значение по умолчанию `"Anonymous"`.
    """

    stub = get_user_stub()

    try:
        response = stub.CreateUser(CreateUserRequest(
            email=payload.email,
            name=payload.name or 'Anonymous'
        ))
        user = response.user
        return UserResponseJSON(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code = 409 if e.code() == grpc.StatusCode.ALREADY_EXISTS else 400,
            detail=f"User Service: {e.details() or 'ошибка'}"
        )

@app.get('/products', response_model=List[ProductResponseJSON])
def list_products():
    """Возвращает список всех товаров из catalog-service.

    Вызывает `ListProducts` без параметров (в текущей версии — полный список).

    Returns:
        List[ProductResponseJSON]: Список товаров.

    Raises:
        HTTPException:
            - 500 (Internal Server Error) при любой gRPC-ошибке (каталог недоступен и т.п.).

    Note:
        В будущем можно расширить поддержкой пагинации/фильтрации через query-параметры.
    """

    stub = get_catalog_stub()

    try:
        response = stub.ListProducts(ListProductsRequest())
        products = []

        for p in response.products:
            products.append(ProductResponseJSON(
                id=p.id,
                name=p.name,
                description=p.description,
                price=p.price,
                currency_code=p.currency_code,
                in_stock=p.in_stock
            ))

        return products

    except grpc.RpcError as e:
        raise HTTPException(500, f"Catalog Service: {e.details() or 'ошибка'}")


@app.post('/cart/items', response_model=dict)
def add_cart_item(payload: AddCartItemJSON):
    """Добавляет товар в корзину указанного пользователя.

    Вызывает `AddItem` в cart-service с валидацией `user_id`, `product_id`, `quantity > 0`.

    Args:
        payload (AddCartItemJSON): Данные для добавления в корзину.

    Returns:
        dict: Простой JSON-ответ `{"status": "OK", "message": "..."}`.

    Raises:
        HTTPException:
            - 400 (Bad Request) при ошибках: несуществующий user/product, отрицательное quantity и т.д.

    Note:
        Ответ не содержит данных о корзине — клиент должен вызвать `/cart?user_id=...` после.
    """

    stub = get_cart_stub()
    try:
        stub.AddItem(AddItemRequest(
            user_id=payload.user_id,
            product_id=payload.product_id,
            quantity=payload.quantity
        ))

        return {
            'status': 'OK',
            'message': 'Товар добавлен в корзину'
            }

    except grpc.RpcError as e:
        raise HTTPException(400, f"Cart Service: {e.details() or 'ошибка'}")


@app.get('/cart', response_model=CartResponseJSON)
def get_cart(user_id: str):
    """Возвращает текущее состояние корзины пользователя.

    Вызывает `GetCart` в cart-service по `user_id`.

    Args:
        user_id (str): UUID пользователя.

    Returns:
        CartResponseJSON: Корзина с товарами, общей суммой и валютой.

    Raises:
        HTTPException:
            - 400 (Bad Request) если `user_id` некорректен или корзина не найдена.

    Note:
        Предполагается, что у пользователя всегда есть корзина (пустая при первом обращении).
    """

    stub = get_cart_stub()

    try:
        response = stub.GetCart(GetCartRequest(user_id=user_id))
        items = []

        for item in response.items:
            items.append(CartItemJSON(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                currency_code=item.currency_code
            ))

        return CartResponseJSON(
            items=items,
            total_amount=response.total_amount,
            currency_code=response.currency_code
        )

    except grpc.RpcError as e:
        raise HTTPException(400, f"Cart Service: {e.details() or 'ошибка'}")


@app.post('/orders', response_model=OrderResponseJSON)
def create_order(payload: CreateOrderJSON):
    """Создаёт заказ на основе текущей корзины пользователя.

    Вызывает `CreateOrder` в order-service. Сервис копирует содержимое корзины,
    резервирует товары (если применимо) и возвращает заказ.

    Args:
        payload (CreateOrderJSON): `user_id` владельца корзины.

    Returns:
        OrderResponseJSON: Созданный заказ с `id`, `status`, `items`, итоговой суммой.

    Raises:
        HTTPException:
            - 404 (Not Found), если пользователь/корзина не найдены.
            - 400 (Bad Request) при нарушении бизнес-правил (например, пустая корзина).
            - 500 (Internal Server Error) при системных сбоях.

    Note:
        В коде есть **ошибка**: `status_str` вычисляется, но не используется — `order.status`
        передаётся как `int`, а в `OrderResponseJSON.status` ожидается `str`.

        Исправление:
            status=status_str  # вместо status=order.status
    """

    stub = get_order_stub()

    try:
        response = stub.CreateOrder(CreateOrderRequest(user_id=payload.user_id))

        order = response.order

        items = []

        for item in order.items:
            items.append(CartItemJSON(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                price=item.price,
                currency_code=item.currency_code
            ))

        status_str = {
            1: 'CREATED',
            2: 'PAID',
            3: 'CANCELED'
        }.get(order.status, 'UNKNOWN')

        return OrderResponseJSON(
            id=order.id,
            user_id=order.user_id,
            status=status_str,
            total_amount=order.total_amount,
            currency_code=order.currency_code,
            items=items
        )

    except grpc.RpcError as e:
        code_map = {
            grpc.StatusCode.NOT_FOUND: 404,
            grpc.StatusCode.INVALID_ARGUMENT: 400,
            grpc.StatusCode.FAILED_PRECONDITION: 400
        }

        status = code_map.get(e.code(), 500)

        raise HTTPException(status, f"Order Service: {e.details() or 'ошибка'}")
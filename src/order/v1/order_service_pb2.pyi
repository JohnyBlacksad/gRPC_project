from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Order(_message.Message):
    __slots__ = ("id", "user_id", "status", "items", "total_amount", "currency_code", "created_at")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATUS_UNSECIFIED: _ClassVar[Order.Status]
        STATUS_CREATED: _ClassVar[Order.Status]
        STATUS_PAID: _ClassVar[Order.Status]
        STATUS_CANCELED: _ClassVar[Order.Status]
    STATUS_UNSECIFIED: Order.Status
    STATUS_CREATED: Order.Status
    STATUS_PAID: Order.Status
    STATUS_CANCELED: Order.Status
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_CODE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    status: Order.Status
    items: _containers.RepeatedCompositeFieldContainer[OrderItem]
    total_amount: int
    currency_code: str
    created_at: int
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., status: _Optional[_Union[Order.Status, str]] = ..., items: _Optional[_Iterable[_Union[OrderItem, _Mapping]]] = ..., total_amount: _Optional[int] = ..., currency_code: _Optional[str] = ..., created_at: _Optional[int] = ...) -> None: ...

class OrderItem(_message.Message):
    __slots__ = ("product_id", "product_name", "quantity", "price", "currency_code")
    PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_NAME_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_CODE_FIELD_NUMBER: _ClassVar[int]
    product_id: str
    product_name: str
    quantity: int
    price: int
    currency_code: str
    def __init__(self, product_id: _Optional[str] = ..., product_name: _Optional[str] = ..., quantity: _Optional[int] = ..., price: _Optional[int] = ..., currency_code: _Optional[str] = ...) -> None: ...

class CreateOrderRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class CreateOrderResponse(_message.Message):
    __slots__ = ("order",)
    ORDER_FIELD_NUMBER: _ClassVar[int]
    order: Order
    def __init__(self, order: _Optional[_Union[Order, _Mapping]] = ...) -> None: ...

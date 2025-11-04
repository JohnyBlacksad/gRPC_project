from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CartItem(_message.Message):
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

class AddItemRequest(_message.Message):
    __slots__ = ("user_id", "product_id", "quantity")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PRODUCT_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    product_id: str
    quantity: int
    def __init__(self, user_id: _Optional[str] = ..., product_id: _Optional[str] = ..., quantity: _Optional[int] = ...) -> None: ...

class AddItemResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetCartRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class GetCartResponse(_message.Message):
    __slots__ = ("items", "total_amount", "currency_code")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_CODE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[CartItem]
    total_amount: int
    currency_code: str
    def __init__(self, items: _Optional[_Iterable[_Union[CartItem, _Mapping]]] = ..., total_amount: _Optional[int] = ..., currency_code: _Optional[str] = ...) -> None: ...

class ClearCartRequset(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class ClearCartResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

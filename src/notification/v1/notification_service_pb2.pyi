from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NotificationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOTIFICATION_TYPE_UNSPECIFIED: _ClassVar[NotificationType]
    NOTIFICATION_TYPE_EMAIL: _ClassVar[NotificationType]
    NOTIFICATION_TYPE_SMS: _ClassVar[NotificationType]
    NOTIFICATION_TYPE_PUSH: _ClassVar[NotificationType]
NOTIFICATION_TYPE_UNSPECIFIED: NotificationType
NOTIFICATION_TYPE_EMAIL: NotificationType
NOTIFICATION_TYPE_SMS: NotificationType
NOTIFICATION_TYPE_PUSH: NotificationType

class SendNotificationRequest(_message.Message):
    __slots__ = ("type", "to", "subject", "body")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    type: NotificationType
    to: str
    subject: str
    body: str
    def __init__(self, type: _Optional[_Union[NotificationType, str]] = ..., to: _Optional[str] = ..., subject: _Optional[str] = ..., body: _Optional[str] = ...) -> None: ...

class SendNotificationResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

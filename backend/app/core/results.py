from typing import Any, Optional, TypeVar, Generic
from enum import Enum

T = TypeVar("T")

class ServiceStatus(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    FAILURE = "FAILURE"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_NAME = "DUPLICATE_NAME"
    RESOURCE_IN_USE = "RESOURCE_IN_USE"
    VERSION_ACTIVE = "VERSION_ACTIVE"
    BAD_REQUEST = "BAD_REQUEST"

class ServiceResult(Generic[T]):
    def __init__(self, status: ServiceStatus, data: Optional[T] = None, message: Optional[str] = None, business_code: Optional[str] = None):
        self.status = status
        self.data = data
        self.message = message
        self.business_code = business_code

    @property
    def success(self) -> bool:
        return self.status == ServiceStatus.SUCCESS

    @classmethod
    def success_result(cls, data: T = None) -> "ServiceResult[T]":
        return cls(ServiceStatus.SUCCESS, data)

    @classmethod
    def failure_result(cls, status: ServiceStatus, message: str = None, business_code: str = None) -> "ServiceResult[T]":
        return cls(status, message=message, business_code=business_code)

    @classmethod
    def not_found(cls, message: str = None) -> "ServiceResult[T]":
        return cls(ServiceStatus.NOT_FOUND, message=message)

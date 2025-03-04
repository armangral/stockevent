from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class Metadata(BaseModel):
    total_elements: int


class Page(BaseModel, Generic[T]):
    data: List[T]
    metadata: Metadata
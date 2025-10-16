from sqlmodel import SQLModel
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')


class Pageable(BaseModel):
    """Pageable request (like Spring Pageable)"""
    page: int = 0
    size: int = 20

    def get_offset(self) -> int:
        return self.page * self.size

    def get_limit(self) -> int:
        return self.size


class Sort(BaseModel):
    """Sort information"""
    property: str
    direction: str = "ASC"  # ASC or DESC


class PageRequest(Pageable):
    """Page request with sort (like Spring PageRequest)"""
    sort: List[Sort] = []


class Slice(SQLModel, Generic[T]):
    """Slice response (like Spring Slice)"""
    content: List[T]
    pageable: Pageable
    size: int
    number: int
    number_of_elements: int
    first: bool
    last: bool
    empty: bool

    class Config:
        arbitrary_types_allowed = True


class Page(Slice[T], Generic[T]):
    """Page response with total count (like Spring Page)"""
    total_elements: int
    total_pages: int

    class Config:
        arbitrary_types_allowed = True

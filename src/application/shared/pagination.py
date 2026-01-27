"""Pagination utilities."""
from dataclasses import dataclass
from typing import List, TypeVar, Generic

T = TypeVar('T')


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


"""Reusable pagination dependency and helpers."""
import math
from typing import Any, Sequence, Type

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.common import Page


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-based)"),
        size: int = Query(10, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def paginate(db: Session, stmt: Select, params: PageParams, options: Sequence = ()) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.options(*options).limit(params.size).offset(params.offset)).unique().all()
    return list(items), total


def build_page(schema: Type[Any], items: Sequence, total: int, params: PageParams) -> Page:
    return Page[schema](
        items=[schema.model_validate(i) for i in items],
        total=total,
        page=params.page,
        size=params.size,
        pages=math.ceil(total / params.size) if total else 0,
    )

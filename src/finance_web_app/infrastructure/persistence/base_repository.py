"""Generic SQLModel repository.

Implements the CRUD shared by every resource once, so concrete repositories only
add resource-specific queries. Unexpected driver failures are wrapped in
``RepositoryError`` and ``get``/``delete`` raise ``NotFoundError`` -- the same
contract the Protocols promise (``docs/ARCHITECTURE.md`` -> "Repository protocol
shape").
"""

from __future__ import annotations

from typing import ClassVar, Generic, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper
from sqlmodel import Session, SQLModel, select

from finance_web_app.core.contracts.errors import NotFoundError, RepositoryError

TModel = TypeVar("TModel", bound=SQLModel)


class SqlModelRepository(Generic[TModel]):
    """Base CRUD against a single SQLModel table, bound to a request session."""

    model: type[TModel]
    resource_name: ClassVar[str]

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[TModel]:
        try:
            primary_key = class_mapper(self.model).primary_key
            statement = select(self.model).order_by(*primary_key)
            return list(self._session.exec(statement).all())
        except SQLAlchemyError as exc:
            raise RepositoryError(f"list {self.resource_name}", exc) from exc

    def get(self, entity_id: int) -> TModel:
        try:
            obj = self._session.get(self.model, entity_id)
        except SQLAlchemyError as exc:
            raise RepositoryError(f"get {self.resource_name}", exc) from exc
        if obj is None:
            raise NotFoundError(self.resource_name, entity_id)
        return obj

    def create(self, record: TModel) -> TModel:
        try:
            self._session.add(record)
            self._session.commit()
            self._session.refresh(record)
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise RepositoryError(f"create {self.resource_name}", exc) from exc
        return record

    def delete(self, entity_id: int) -> None:
        obj = self.get(entity_id)
        try:
            self._session.delete(obj)
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise RepositoryError(f"delete {self.resource_name}", exc) from exc

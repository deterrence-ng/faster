#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2021-05-06 13:46:25
# @Author  : Dahir Muhammad Dahir
# @Description : taken from Bill's template codebase

# pyright: ignore
import ulid

import inflect

from sqlalchemy import Date, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.functions import func
from datetime import date as dt, datetime
from typing import Any, Optional

get_plural = inflect.engine()


def get_new_ulid() -> str:
    return ulid.ulid()


class BaseMixin:
    __allow_unmapped__ = True

    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        plural_name: str = get_plural.plural_noun(cls.__name__.lower())  # type: ignore
        return plural_name

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    uuid: Mapped[str] = mapped_column(
        String(length=50), unique=True, nullable=False, default=get_new_ulid
    )
    date: Mapped[dt | None] = mapped_column(
        Date,
        index=True,
        default=dt.today,
        nullable=True,
        server_default=func.current_date(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, server_default=func.now(), nullable=False
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    __mapper_args__ = {"eager_defaults": True}


class BaseUACMixin(BaseMixin):
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)


class BaseModelMixin(BaseMixin):
    @declared_attr
    def created_by(cls: Any) -> Mapped[str]:
        return mapped_column(String(50), ForeignKey("users.uuid"), nullable=False)

    @declared_attr
    def creator(cls: Any) -> Mapped[Optional["User"]]:  # type: ignore # noqa
        return relationship("User", lazy="joined")

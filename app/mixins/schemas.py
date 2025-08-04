#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2024-10-19 13:34:08
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from enum import Enum
from app.utils.enums import ActionStatus
from datetime import datetime, date as dt_date
from typing import Any
from pydantic import BaseModel, EmailStr, ConfigDict, computed_field


class BaseSchemaMixin(BaseModel):
    id: int
    uuid: str
    date: dt_date
    created_at: datetime
    last_modified: datetime

    model_config = ConfigDict(from_attributes=True)


class BaseUACSchemaMixin(BaseSchemaMixin):
    name: str
    description: str | None = None


class UserMin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    firstname: str
    lastname: str
    middlename: str | None = ""


class Processor(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    firstname: str
    lastname: str
    middlename: str | None = ""


class BaseModelOut(BaseSchemaMixin):
    created_by: str

    creator: UserMin


class BaseModelMin(BaseSchemaMixin):
    pass


class BaseModelIn(BaseModel):
    model_config = ConfigDict(str_max_length=6144)


class BaseModelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrderType(str, Enum):
    asc = "asc"
    desc = "desc"


class BaseModelFilter(BaseModelIn):
    model_config = ConfigDict(str_to_upper=False)
    skip: int = 0
    limit: int = 10
    order: OrderType = OrderType.asc


class JoinSearch(BaseModel):
    model: Any
    column: str
    onkey: str


class BaseModelSearch(BaseModelIn):
    model_config = ConfigDict(str_to_upper=False)
    search_term: str
    skip: int = 0
    limit: int = 10
    order: OrderType = OrderType.asc

    @computed_field
    @property
    def search_fields(self) -> list[str]:
        return []

    @computed_field
    @property
    def join_search(self) -> list[JoinSearch]:
        return []


class BaseModelCreate(BaseModel):
    created_by: str


class Status(BaseModel):
    status: ActionStatus

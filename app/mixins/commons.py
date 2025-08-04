#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2024-10-18 20:01:07
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from app.utils.custom_validators import Money, UpStr
from enum import Enum
from typing import Any


from app.mixins.schemas import BaseSchemaMixin
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import date


class Gender(str, Enum):
    male = "m"
    female = "f"
    na = "na"


class UserOut(BaseSchemaMixin):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    firstname: UpStr
    lastname: UpStr
    middlename: UpStr | None = ""
    is_active: bool
    is_system_user: bool


class DateRange(BaseModel):
    column_name: str = "date"
    from_date: date
    to_date: date


class ListBase(BaseModel):
    count: int
    sum: Money | None = None


class FilterBase(BaseModel):
    skip: int
    limit: int


class UserMin(BaseSchemaMixin):
    email: str
    firstname: UpStr
    lastname: UpStr
    middlename: UpStr | None = ""
    phone: str | None


class UserPublic(BaseModel):
    uuid: str
    email: str
    firstname: UpStr
    lastname: UpStr
    middlename: UpStr | None = ""
    phone: str | None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Any):
        # obfuscate parts of the email with asterisks
        email_parts = value.split("@")
        email_parts[0] = email_parts[0][:5] + "*" * (len(email_parts[0]) - 5)
        email_parts[1] = email_parts[1][:5] + "*" * (len(email_parts[1]) - 5)
        return "@".join(email_parts)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Any):
        # obfuscate the middle part of the phone with asterisks
        return value[:5] + "*" * (len(value) - 5) + value[-2:]


class Token(BaseModel):
    access_token: str
    token_type: str
    user_group: str | None = ""
    permissions: list[str] | None = None

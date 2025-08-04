#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2024-10-20 07:36:29
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from typing import List, Optional
from fastapi import HTTPException
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationInfo,
    computed_field,
    field_validator,
)

from app.mixins.commons import ListBase

from app.mixins.schemas import BaseModelPublic, BaseSchemaMixin
from app.access_control.schemas import GroupSchema, GroupOutSchema
from app.utils.custom_validators import Phone, UpStr
from app.utils.misc import gen_email, gen_random_password, gen_random_phone
from app.utils.user import get_password_hash


class UserIn(BaseModel):
    email: EmailStr | None = Field(
        default_factory=gen_email, description="Email address of the user"
    )
    firstname: UpStr
    lastname: UpStr
    middlename: UpStr | None = None
    phone: str | None = Field(
        default_factory=gen_random_phone, description="Phone number of the user"
    )
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    temp_password_hash: str = ""
    password: str
    password_hash: str
    firstname: str | None = None
    lastname: str | None = None
    middlename: str | None = None
    is_admin: bool
    can_login: bool = True
    phone: Phone

    @field_validator("password")
    @classmethod
    def _gen_password(cls, val: str) -> str:
        if val:
            return val

        return gen_random_password()

    @field_validator("password_hash")
    @classmethod
    def _hash_password(cls, val: str, info: ValidationInfo) -> str:
        return get_password_hash(info.data["password"])

    @computed_field
    @property
    def is_temp_email(self) -> bool:
        return self.email.endswith("@diacyber.com")

    @computed_field
    @property
    def is_temp_phone(self) -> bool:
        return self.phone.startswith("4134") if self.phone else False

    @computed_field
    @property
    def fullname(self) -> str:
        return f"{self.firstname if self.firstname else ''} {self.middlename if self.middlename else ''} {self.lastname if self.lastname else ''}".strip()


class UserGroup(BaseModel):
    groups: List[str]


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    firstname: UpStr | None = None
    lastname: UpStr | None = None
    middlename: UpStr | None = None
    is_active: bool | None = None
    phone: str | None = None


class UserUpdateSelf(BaseModel):
    firstname: UpStr | None = None
    lastname: UpStr | None = None
    middlename: UpStr | None = None


class UserActivate(BaseModel):
    password: str
    password_hash: str
    can_login: bool = True

    @field_validator("password")
    @classmethod
    def _gen_password(cls, val: str) -> str:
        return gen_random_password()

    @field_validator("password_hash")
    @classmethod
    def _hash_password(cls, val: str, info: ValidationInfo) -> str:
        return get_password_hash(info.data["password"])


class AdminUserFilter(BaseModel):
    email: EmailStr | None = None
    firstname: UpStr | None = None
    lastname: UpStr | None = None
    middlename: UpStr | None = None
    user_group_name: str | None = None
    is_active: bool | None = None
    phone: str | None = None


class ChangePasswordFromDashboard(BaseModel):
    current_password: str
    new_password: str


class UserSchema(BaseSchemaMixin):
    email: EmailStr
    firstname: UpStr
    lastname: UpStr
    middlename: UpStr | None = ""
    is_active: bool
    is_admin: bool
    phone: str | None = None
    groups: list[GroupSchema] | None = None

    @property
    def permissions(self) -> List[str]:
        perms: list[str] = []
        if self.groups is None:
            return perms

        for group in self.groups:
            for role in group.roles:
                for perm in role.permissions:
                    perms.append(perm.name)
        return list(set(perms))

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


class UserOut(BaseSchemaMixin):
    email: EmailStr
    firstname: UpStr
    lastname: UpStr
    middlename: Optional[UpStr] = ""
    is_active: bool
    is_admin: bool
    groups: List[GroupOutSchema]


class UserPublic(BaseModelPublic):
    firstname: UpStr
    lastname: UpStr
    middlename: Optional[UpStr] = ""


class UserList(ListBase):
    items: list[UserOut]


class ResetPassword(BaseModel):
    password: str


class PasswordChangeOut(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_group: str | None = ""
    permissions: list[str] | None = None


class Login(BaseModel):
    email_or_phone: str = Field(
        description="Email address or phone number of the user",
        pattern="^[0-9a-zA-Z@.]+$",
    )
    password: str


class PasswordResetRequest(BaseModel):
    """PasswordResetRequest
    Either email or phone is required to reset the password.
    If both are provided, email will be used.
    If neither is provided, an error will be raised.
    """

    email: EmailStr | None = None
    phone: Phone | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str, info: ValidationInfo) -> str:
        # either email or phone is required
        if not value and not info.data.get("email"):
            raise HTTPException(
                status_code=400, detail="Either email or phone is required"
            )

        return value


class PasswordResetVerifyOTP(BaseModel):
    """PasswordResetVerifyOTP
    only one of email or phone is required to verify the OTP.
    if both are provided, error will be raised.
    """

    email: EmailStr | None = None
    phone: Phone | None = None
    otp: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str, info: ValidationInfo) -> str:
        # either email or phone is required but not both
        if not value and not info.data.get("email"):
            raise HTTPException(
                status_code=400, detail="Either email or phone is required"
            )

        if value and info.data.get("email"):
            raise HTTPException(
                status_code=400, detail="Either email or phone is required but not both"
            )

        return value


class PasswordReset(BaseModel):
    password_or_pin: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

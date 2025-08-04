#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2023-01-17 10:51:44
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from pydantic import BaseModel
from app.mixins.commons import ListBase

from app.mixins.schemas import BaseUACSchemaMixin
from app.utils.custom_validators import LowStr


class PermissionCreate(BaseModel):
    name: str
    description: LowStr | None = None


class PermissionUpdate(BaseModel):
    name: str | None = None
    description: LowStr | None = None


class PermissionSchema(BaseUACSchemaMixin):
    pass


class PermissionList(ListBase):
    items: list[PermissionSchema]


class RoleCreate(BaseModel):
    name: str
    description: LowStr | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: LowStr | None = None
    permissions: list[str] | None


class RemoveRolePermission(BaseModel):
    permissions: list[str]


class RoleSchema(BaseUACSchemaMixin):
    permissions: list[PermissionSchema]


class RoleList(ListBase):
    items: list[RoleSchema]


class GroupCreate(BaseModel):
    name: str
    description: LowStr | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: LowStr | None = None
    roles: list[str] | None


class RemoveGroupRole(BaseModel):
    roles: list[str]


class GroupSchema(BaseUACSchemaMixin):
    roles: list[RoleSchema]


class GroupList(ListBase):
    items: list[GroupSchema]


class GroupOutSchema(BaseUACSchemaMixin):
    pass

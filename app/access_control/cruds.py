#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2023-01-17 10:44:39
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from typing import Any
from app.access_control import models, schemas
from app.utils.crud_util import CrudUtil
from sync_perms import main as create_and_sync_perms


def sync_permissions() -> Any:

    create_and_sync_perms()


async def create_permission(
    cu: CrudUtil, perm_data: schemas.PermissionCreate
) -> models.Permission:
    await cu.ensure_unique(models.Permission, {"name": perm_data.name})
    permission: models.Permission = await cu.create_model(models.Permission, perm_data)
    return permission


async def get_perm_by_name(cu: CrudUtil, name: str) -> models.Permission:

    permission: models.Permission = await cu.get_model_or_404(
        models.Permission, {"name": name}
    )
    return permission


async def update_permission(
    cu: CrudUtil,
    name: str,
    update_data: schemas.PermissionUpdate,
) -> models.Permission:

    permission: models.Permission = await cu.update_model(
        model_to_update=models.Permission,
        update=update_data,
        update_conditions={"name": name},
    )

    return permission


async def list_permission(
    cu: CrudUtil,
    skip: int,
    limit: int,
) -> schemas.PermissionList:

    permissions: dict[str, Any] = await cu.list_model(
        model_to_list=models.Permission, skip=skip, limit=limit
    )

    return schemas.PermissionList(**permissions)


async def delete_permission(
    cu: CrudUtil,
    name: str,
) -> dict[str, Any]:
    return await cu.delete_model(
        model_to_delete=models.Permission, delete_conditions={"name": name}
    )


async def create_role(cu: CrudUtil, role_data: schemas.RoleCreate) -> models.Role:

    await cu.ensure_unique(
        model_to_check=models.Role, unique_condition={"name": role_data.name}
    )

    role: models.Role = await cu.create_model(
        model_to_create=models.Role, create=role_data
    )

    return role


async def get_role_by_name(
    cu: CrudUtil,
    name: str,
) -> models.Role:

    role: models.Role = await cu.get_model_or_404(
        model_to_get=models.Role, model_conditions={"name": name}
    )
    return role


async def update_role(
    cu: CrudUtil,
    name: str,
    update_data: schemas.RoleUpdate,
) -> models.Role:

    role: models.Role = await cu.update_model(
        model_to_update=models.Role,
        update=update_data,
        update_conditions={"name": name},
        autocommit=False if update_data.permissions else True,
    )

    if update_data.permissions:
        for perm_name in update_data.permissions:
            role.permissions.append(await get_perm_by_name(cu=cu, name=perm_name))

    await cu.db.commit()
    await cu.db.refresh(role)

    return role


async def list_role(cu: CrudUtil, skip: int, limit: int) -> schemas.RoleList:
    roles: dict[str, Any] = await cu.list_model(
        model_to_list=models.Role, skip=skip, limit=limit
    )

    return schemas.RoleList(**roles)


async def delete_role(cu: CrudUtil, name: str) -> dict[str, Any]:
    return await cu.delete_model(
        model_to_delete=models.Role, delete_conditions={"name": name}
    )


async def create_group(cu: CrudUtil, group_data: schemas.GroupCreate) -> models.Group:

    await cu.ensure_unique(
        model_to_check=models.Group, unique_condition={"name": group_data.name}
    )

    group: models.Group = await cu.create_model(
        model_to_create=models.Group, create=group_data
    )

    return group


async def get_group_by_name(cu: CrudUtil, name: str) -> models.Group:
    group: models.Group = await cu.get_model_or_404(
        model_to_get=models.Group, model_conditions={"name": name}
    )
    return group


async def update_group(
    cu: CrudUtil,
    name: str,
    update_data: schemas.GroupUpdate,
) -> models.Group:

    group: models.Group = await cu.update_model(
        model_to_update=models.Group,
        update=update_data,
        update_conditions={"name": name},
        autocommit=False if update_data.roles else True,
    )

    if update_data.roles:
        for role_name in update_data.roles:
            group.roles.append(await get_role_by_name(cu=cu, name=role_name))

    await cu.db.commit()
    await cu.db.refresh(group)

    return group


async def list_group(
    cu: CrudUtil,
    skip: int,
    limit: int,
) -> schemas.GroupList:

    groups: dict[str, Any] = await cu.list_model(
        model_to_list=models.Group, skip=skip, limit=limit
    )

    return schemas.GroupList(**groups)


async def delete_group(
    cu: CrudUtil,
    name: str,
) -> dict[str, Any]:
    return await cu.delete_model(
        model_to_delete=models.Group, delete_conditions={"name": name}
    )

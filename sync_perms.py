#!/usr/bin/env python
# -=-<[ Bismillahirrahmanirrahim ]>-=-
# -*- coding: utf-8 -*-
# @Date    : 2023-01-24 18:52:40
# @Author  : Dahir Muhammad Dahir (dahirmuhammad3@gmail.com)
# @Link    : link
# @Version : 1.0.0


from sqlalchemy.orm import Session

from app.access_control import models
from app.config.database import SessionLocal
from app.utils.misc import find_perms


def create_and_sync_perms(db: Session, perms: list[str]) -> None:
    to_create: dict[str, list[str]] = {}
    perm_to_create: list[models.Permission] = []
    role_to_create: list[models.Role] = []

    for perm in set(perms):
        db_perm = (
            db.query(models.Permission).filter(models.Permission.name == perm).first()
        )

        if not db_perm:
            perm_prefix = perm.split(":")[0]
            role = f"{perm_prefix}:owner"
            if role not in to_create:
                to_create[role] = []

            to_create[role].append(perm)

    for role, perms in to_create.items():
        db_role = db.query(models.Role).filter(models.Role.name == role).first()
        if not db_role:
            db_role = models.Role(name=role)  # type: ignore

        for perm in perms:
            db_perm = (
                db.query(models.Permission)
                .filter(models.Permission.name == perm)
                .first()
            )
            if not db_perm:
                db_perm = models.Permission(name=perm)  # type: ignore
                perm_to_create.append(db_perm)

            db_role.permissions.append(db_perm)

        role_to_create.append(db_role)

    print(
        f"the following permissions will be created: \
        {[perm.name for perm in perm_to_create]}"
    )

    print(
        f"the following roles will be created: \
        {[role.name for role in role_to_create]}"
    )

    # check if super_admin_group exists, if not create it, otherwise return and
    # add perms to it
    super_admin_group = (
        db.query(models.Group).filter(models.Group.name == "super_admin_group").first()
    )

    if not super_admin_group:
        super_admin_group = models.Group(name="super_admin_group")  # type: ignore

    for role in role_to_create:
        super_admin_group.roles.append(role)

    db.add_all([*perm_to_create, *role_to_create, super_admin_group])
    db.commit()


def main() -> None:
    db: Session = SessionLocal()
    create_and_sync_perms(db, find_perms())
    db.close()


if __name__ == "__main__":
    main()

from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from passlib import pwd

from app.user import models as users_models
from app.access_control import models as ac_models
from app.utils.user import get_password_hash
from app.config.config import settings


def init_db(db: Session) -> None:
    # check if database has already been initialized
    if settings.environment == "PRODUCTION":
        print("==================================================")
        print("Production Environment. Skipping Initialization...")
        print("==================================================")
        return

    if db.query(users_models.User).first():
        print("=========================================")
        print("Database already initialized. Skipping...")
        print("=========================================")
        return

    print("=========================================")
    print("Initializing database...")
    print("=========================================")

    if settings.environment == "LOCALDOCKER" or settings.environment == "STAGING":
        email = settings.initial_email
        password = settings.initial_password
        firstname = settings.initial_firstname
        lastname = settings.initial_lastname
        middlename = settings.initial_middlename
    else:
        while True:
            email = input("Enter superadmin email: ")
            if len(email) > 0:
                try:
                    validate_email(email)
                except EmailNotValidError:
                    print("Email is not valid! Please provide a valid email.\n")
                else:
                    break

        password = pwd.genword(100)
        print(f"Generated password: {password} for {email} keep it safe")

        firstname = input("Enter superadmin firstname [Super]: ")
        lastname = input("Enter superadmin lastname [Admin]: ")
        middlename = input("Enter superadmin middle name: ")

    user_dict = {
        "email": email,
        "firstname": firstname.upper() if firstname else "SUPER",
        "lastname": lastname.upper() if lastname else "ADMIN",
        "middlename": middlename.upper() if middlename else None,
        "password_hash": get_password_hash(password),
        "is_admin": True,
    }

    perms = [
        "permission:create",
        "permission:read",
        "permission:update",
        "permission:list",
        "permission:delete",
        "permission:sync",
    ]

    role_perms = [
        "role:create",
        "role:read",
        "role:update",
        "role:list",
        "role:delete",
    ]

    group_perms = [
        "group:create",
        "group:read",
        "group:update",
        "group:list",
        "group:delete",
    ]

    admin_perms = [
        "admin:create",
        "admin:read",
        "admin:update",
        "admin:list",
        "admin:delete",
    ]

    """
    Possible roles:
    - owner
    - creator
    - editor
    - viewer
    - lister
    - deleter
    """
    perm_owner = ac_models.Role(name="permission:owner")  # type: ignore
    role_owner = ac_models.Role(name="role:owner")  # type: ignore
    group_owner = ac_models.Role(name="group:owner")  # type: ignore
    admin_owner = ac_models.Role(name="admin:owner")  # type: ignore

    for perm_name in perms:
        perm = ac_models.Permission(name=perm_name)  # type: ignore
        perm_owner.permissions.append(perm)
        db.add(perm)

    for perm_name in role_perms:
        perm = ac_models.Permission(name=perm_name)  # type: ignore
        role_owner.permissions.append(perm)
        db.add(perm)

    for perm_name in group_perms:
        perm = ac_models.Permission(name=perm_name)  # type: ignore
        group_owner.permissions.append(perm)
        db.add(perm)

    for perm_name in admin_perms:
        perm = ac_models.Permission(name=perm_name)  # type: ignore
        admin_owner.permissions.append(perm)
        db.add(perm)

    super_admin_group = ac_models.Group(name="super_admin_group")  # type: ignore
    super_admin_group.roles.append(perm_owner)
    super_admin_group.roles.append(role_owner)
    super_admin_group.roles.append(group_owner)
    super_admin_group.roles.append(admin_owner)

    user = users_models.User(**user_dict)
    user.groups.append(super_admin_group)

    db.add_all([perm_owner, role_owner, group_owner, super_admin_group, user])

    db.commit()

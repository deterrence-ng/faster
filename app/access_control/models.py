from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql.sqltypes import String

from app.config.database import Base
from app.mixins.columns import BaseUACMixin


# Many to Many associations
permission_role = Table(
    "permission_role",
    Base.metadata,
    Column("permission_id", String(length=50), ForeignKey("permissions.uuid")),
    Column("role_id", String(length=50), ForeignKey("roles.uuid")),
)
role_group = Table(
    "role_group",
    Base.metadata,
    Column("role_id", String(length=50), ForeignKey("roles.uuid")),
    Column("group_id", String(length=50), ForeignKey("groups.uuid")),
)


class Permission(BaseUACMixin, Base):
    pass


class Role(BaseUACMixin, Base):
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=permission_role, uselist=True, lazy="joined"
    )


class Group(BaseUACMixin, Base):
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=role_group, uselist=True, lazy="joined"
    )

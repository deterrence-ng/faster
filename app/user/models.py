from datetime import datetime, date
from sqlalchemy import Boolean, Column, DateTime, Date, ForeignKey, String, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.access_control.models import Group
from app.config.database import Base
from app.mixins.columns import BaseMixin
import ulid

from app.utils.misc import gen_random_secret_key

user_group = Table(
    "user_group",
    Base.metadata,
    Column("group_id", String(length=50), ForeignKey("groups.uuid")),
    Column("user_id", String(length=50), ForeignKey("users.uuid")),
)


class User(BaseMixin, Base):
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    old_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    temp_password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    firstname: Mapped[str] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255))
    middlename: Mapped[str | None] = mapped_column(String(255))
    fullname: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None, server_default=None
    )
    phone: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    nin: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, default=None
    )
    bvn: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, default=None
    )
    date_of_birth: Mapped[date | None] = mapped_column(
        Date, nullable=True, default=None
    )
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    can_login: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )
    is_temp_email: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    is_temp_phone: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    is_profile_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )
    access_key: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, default=ulid.ulid
    )
    validation_key: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, default=gen_random_secret_key
    )

    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary=user_group, uselist=True, lazy="joined"
    )


class PasswordReset(BaseMixin, Base):
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires: Mapped[datetime] = mapped_column(DateTime, nullable=False)

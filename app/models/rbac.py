from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, Boolean

from app.database.session import Base


class BusinessElement(Base):
    __tablename__ = "business_elements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class AccessRule(Base):
    __tablename__ = "access_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    business_element_id: Mapped[int] = mapped_column(ForeignKey("business_elements.id"), nullable=False)
    business_element: Mapped[BusinessElement] = relationship(backref="access_rules")
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role = relationship("Role")

    read_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    read_all_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    create_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    update_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    update_all_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    delete_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    delete_all_permission: Mapped[bool] = mapped_column(Boolean, default=False)

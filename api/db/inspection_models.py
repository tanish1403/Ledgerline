"""Inspection flags ORM model for human approval gate."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.db.models import Base


class InspectionFlag(Base):
    """Consequential action inspection flag with approval lifecycle."""

    __tablename__ = "inspection_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of unit IDs
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="requested", index=True)  # requested | approved | rejected | applied | rolled_back
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    decided_at: Mapped[str] = mapped_column(String(50), nullable=True)
    applied_at: Mapped[str] = mapped_column(String(50), nullable=True)
    rolled_back_at: Mapped[str] = mapped_column(String(50), nullable=True)

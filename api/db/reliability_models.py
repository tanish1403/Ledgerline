"""Engine cycles and engine life ORM models for C-MAPSS turbofan data."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.db.models import Base


class EngineCycle(Base):
    """Engine operational cycles from C-MAPSS dataset."""

    __tablename__ = "engine_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cycle: Mapped[int] = mapped_column(Integer, nullable=False)
    setting_1: Mapped[float] = mapped_column(Float, nullable=True)
    setting_2: Mapped[float] = mapped_column(Float, nullable=True)
    setting_3: Mapped[float] = mapped_column(Float, nullable=True)


class EngineLife(Base):
    """Engine remaining useful life (RUL) / time-to-failure records."""

    __tablename__ = "engine_life"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    time_to_failure: Mapped[float] = mapped_column(Float, nullable=False)
    event_observed: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 = failure, 0 = censored

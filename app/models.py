"""SQLAlchemy models for jshop backend."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
  __tablename__ = "categories"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
  label: Mapped[str] = mapped_column(String(128))
  sort_order: Mapped[int] = mapped_column(Integer, default=0)

  lots: Mapped[list[Lot]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Lot(Base):
  __tablename__ = "lots"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
  name: Mapped[str] = mapped_column(String(255), index=True)
  category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
  price: Mapped[int] = mapped_column(Integer, default=0)
  description: Mapped[str] = mapped_column(Text, default="")
  specs: Mapped[list[str]] = mapped_column(JSON, default=list)
  images: Mapped[list[str]] = mapped_column(JSON, default=list)
  featured: Mapped[bool] = mapped_column(Boolean, default=False)
  sold: Mapped[bool] = mapped_column(Boolean, default=False)
  glitch_background: Mapped[str] = mapped_column(String(255), default="")
  sort_order: Mapped[int] = mapped_column(Integer, default=0)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )

  category: Mapped[Category] = relationship(back_populates="lots")


class ContactChannel(Base):
  __tablename__ = "contact_channels"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
  label: Mapped[str] = mapped_column(String(128))
  hint: Mapped[str] = mapped_column(String(255), default="")
  url_template: Mapped[str] = mapped_column(String(512), default="")
  subject_template: Mapped[str] = mapped_column(String(255), default="")
  body_template: Mapped[str] = mapped_column(Text, default="")
  is_external: Mapped[bool] = mapped_column(Boolean, default=True)
  icon_svg: Mapped[str] = mapped_column(Text, default="")
  sort_order: Mapped[int] = mapped_column(Integer, default=0)

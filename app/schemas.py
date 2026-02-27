"""Pydantic schemas for request and response bodies."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
  code: str = Field(min_length=1, max_length=64)
  label: str = Field(min_length=1, max_length=128)
  sort_order: int = 0


class CategoryCreate(CategoryBase):
  pass


class CategoryUpdate(BaseModel):
  label: str | None = Field(default=None, min_length=1, max_length=128)
  sort_order: int | None = None


class CategoryOut(CategoryBase):
  model_config = ConfigDict(from_attributes=True)


class ContactBase(BaseModel):
  code: str = Field(min_length=1, max_length=64)
  label: str = Field(min_length=1, max_length=128)
  hint: str = ""
  url_template: str = ""
  subject_template: str = ""
  body_template: str = ""
  is_external: bool = True
  icon_svg: str = ""
  sort_order: int = 0


class ContactCreate(ContactBase):
  pass


class ContactUpdate(BaseModel):
  label: str | None = Field(default=None, min_length=1, max_length=128)
  hint: str | None = None
  url_template: str | None = None
  subject_template: str | None = None
  body_template: str | None = None
  is_external: bool | None = None
  icon_svg: str | None = None
  sort_order: int | None = None


class ContactOut(ContactBase):
  model_config = ConfigDict(from_attributes=True)


class LotBase(BaseModel):
  slug: str = Field(min_length=1, max_length=128)
  name: str = Field(min_length=1, max_length=255)
  category_code: str = Field(min_length=1, max_length=64)
  price: int = Field(ge=0)
  description: str = ""
  specs: list[str] = Field(default_factory=list)
  images: list[str] = Field(default_factory=list)
  featured: bool = False
  sold: bool = False
  glitch_background: str = ""
  sort_order: int = 0


class LotCreate(LotBase):
  pass


class LotUpdate(BaseModel):
  slug: str | None = Field(default=None, min_length=1, max_length=128)
  name: str | None = Field(default=None, min_length=1, max_length=255)
  category_code: str | None = Field(default=None, min_length=1, max_length=64)
  price: int | None = Field(default=None, ge=0)
  description: str | None = None
  specs: list[str] | None = None
  images: list[str] | None = None
  featured: bool | None = None
  sold: bool | None = None
  glitch_background: str | None = None
  sort_order: int | None = None


class LotOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  slug: str
  name: str
  category_code: str
  category_label: str
  price: int
  description: str
  specs: list[str]
  images: list[str]
  featured: bool
  sold: bool
  glitch_background: str
  sort_order: int
  created_at: datetime | None = None
  updated_at: datetime | None = None


class LotsPage(BaseModel):
  items: list[LotOut]
  total: int
  page: int
  page_size: int
  pages: int


class AdminDashboard(BaseModel):
  lots_total: int
  lots_sold: int
  lots_available: int
  categories_total: int
  contacts_total: int


class BootstrapResponse(BaseModel):
  lots: list[LotOut]
  category_labels: dict[str, str]
  glitch_backgrounds: list[str]
  contacts: list[ContactOut]

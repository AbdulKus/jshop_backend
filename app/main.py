"""FastAPI app for jshop backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from math import ceil

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .database import Base, engine, get_db, SessionLocal
from .seed import load_seed_data, seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
  Base.metadata.create_all(bind=engine)
  with SessionLocal() as db:
    seed_if_empty(db)
  yield


app = FastAPI(
  title="jshop backend",
  version="1.0.0",
  description="Backend API for storefront and admin panel.",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


def normalize_page(page: int, page_size: int) -> tuple[int, int]:
  page = max(page, 1)
  page_size = max(1, min(page_size, 100))
  return page, page_size


def lot_to_schema(lot: models.Lot) -> schemas.LotOut:
  category = lot.category
  category_code = category.code if category else ""
  category_label = category.label if category else category_code
  return schemas.LotOut(
    slug=lot.slug,
    name=lot.name,
    category_code=category_code,
    category_label=category_label,
    price=lot.price,
    description=lot.description,
    specs=list(lot.specs or []),
    images=list(lot.images or []),
    featured=lot.featured,
    sold=lot.sold,
    glitch_background=lot.glitch_background or "",
    sort_order=lot.sort_order,
    created_at=lot.created_at,
    updated_at=lot.updated_at,
  )


def create_lot_model(payload: schemas.LotCreate, category_id: int) -> models.Lot:
  return models.Lot(
    slug=payload.slug,
    name=payload.name,
    category_id=category_id,
    price=payload.price,
    description=payload.description,
    specs=payload.specs,
    images=payload.images,
    featured=payload.featured,
    sold=payload.sold,
    glitch_background=payload.glitch_background,
    sort_order=payload.sort_order,
  )


def category_by_code_or_404(db: Session, category_code: str) -> models.Category:
  category = db.scalar(select(models.Category).where(models.Category.code == category_code))
  if category is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{category_code}' not found")
  return category


def lot_by_slug_or_404(db: Session, slug: str) -> models.Lot:
  lot = db.scalar(
    select(models.Lot).options(joinedload(models.Lot.category)).where(models.Lot.slug == slug)
  )
  if lot is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot '{slug}' not found")
  return lot


def contact_by_code_or_404(db: Session, code: str) -> models.ContactChannel:
  contact = db.scalar(select(models.ContactChannel).where(models.ContactChannel.code == code))
  if contact is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contact '{code}' not found")
  return contact


def apply_lot_filters(
  stmt: Select,
  q: str | None,
  category: str | None,
  only_available: bool,
) -> Select:
  filters = []

  if q:
    search = f"%{q.strip()}%"
    filters.append(
      or_(
        models.Lot.name.ilike(search),
        models.Lot.description.ilike(search),
      )
    )

  if category and category != "all":
    filters.append(models.Category.code == category)

  if only_available:
    filters.append(models.Lot.sold.is_(False))

  if filters:
    stmt = stmt.where(and_(*filters))

  return stmt


def apply_lot_sort(stmt: Select, sort: str) -> Select:
  if sort == "price-asc":
    return stmt.order_by(models.Lot.price.asc(), models.Lot.name.asc())
  if sort == "price-desc":
    return stmt.order_by(models.Lot.price.desc(), models.Lot.name.asc())
  if sort == "name-asc":
    return stmt.order_by(models.Lot.name.asc())
  if sort == "newest":
    return stmt.order_by(models.Lot.created_at.desc(), models.Lot.name.asc())
  return stmt.order_by(models.Lot.featured.desc(), models.Lot.price.asc(), models.Lot.sort_order.asc())


@app.get("/health")
def health() -> dict[str, str]:
  return {"status": "ok"}


@app.get("/api/v1/bootstrap", response_model=schemas.BootstrapResponse)
def get_bootstrap(db: Session = Depends(get_db)) -> schemas.BootstrapResponse:
  lots_stmt = (
    select(models.Lot)
    .options(joinedload(models.Lot.category))
    .join(models.Category)
    .order_by(models.Lot.sort_order.asc(), models.Lot.name.asc())
  )
  lots = db.scalars(lots_stmt).all()

  categories = db.scalars(select(models.Category).order_by(models.Category.sort_order.asc())).all()
  contacts = db.scalars(
    select(models.ContactChannel).order_by(models.ContactChannel.sort_order.asc(), models.ContactChannel.code.asc())
  ).all()

  category_labels = {"all": "Все"}
  for category in categories:
    category_labels[category.code] = category.label

  seed_data = load_seed_data()
  glitch_backgrounds = list(seed_data.get("glitch_backgrounds", []))

  return schemas.BootstrapResponse(
    lots=[lot_to_schema(lot) for lot in lots],
    category_labels=category_labels,
    glitch_backgrounds=glitch_backgrounds,
    contacts=[schemas.ContactOut.from_orm(contact) for contact in contacts],
  )


@app.get("/api/v1/lots", response_model=schemas.LotsPage)
def get_lots(
  q: str | None = Query(default=None),
  category: str | None = Query(default="all"),
  sort: str = Query(default="featured"),
  only_available: bool = Query(default=False),
  page: int = Query(default=1),
  page_size: int = Query(default=8),
  db: Session = Depends(get_db),
) -> schemas.LotsPage:
  page, page_size = normalize_page(page, page_size)

  count_stmt = select(func.count(models.Lot.id)).select_from(models.Lot).join(models.Category)
  count_stmt = apply_lot_filters(count_stmt, q=q, category=category, only_available=only_available)
  total = int(db.scalar(count_stmt) or 0)

  lots_stmt = select(models.Lot).options(joinedload(models.Lot.category)).join(models.Category)
  lots_stmt = apply_lot_filters(lots_stmt, q=q, category=category, only_available=only_available)
  lots_stmt = apply_lot_sort(lots_stmt, sort=sort)
  lots_stmt = lots_stmt.offset((page - 1) * page_size).limit(page_size)

  items = db.scalars(lots_stmt).all()
  pages = max(1, ceil(total / page_size))

  return schemas.LotsPage(
    items=[lot_to_schema(lot) for lot in items],
    total=total,
    page=page,
    page_size=page_size,
    pages=pages,
  )


@app.get("/api/v1/lots/{slug}", response_model=schemas.LotOut)
def get_lot(slug: str, db: Session = Depends(get_db)) -> schemas.LotOut:
  lot = lot_by_slug_or_404(db, slug)
  return lot_to_schema(lot)


@app.get("/api/v1/admin/dashboard", response_model=schemas.AdminDashboard)
def admin_dashboard(db: Session = Depends(get_db)) -> schemas.AdminDashboard:
  lots_total = int(db.scalar(select(func.count(models.Lot.id))) or 0)
  lots_sold = int(db.scalar(select(func.count(models.Lot.id)).where(models.Lot.sold.is_(True))) or 0)
  categories_total = int(db.scalar(select(func.count(models.Category.id))) or 0)
  contacts_total = int(db.scalar(select(func.count(models.ContactChannel.id))) or 0)

  return schemas.AdminDashboard(
    lots_total=lots_total,
    lots_sold=lots_sold,
    lots_available=max(0, lots_total - lots_sold),
    categories_total=categories_total,
    contacts_total=contacts_total,
  )


@app.get("/api/v1/admin/lots", response_model=list[schemas.LotOut])
def admin_list_lots(
  q: str | None = Query(default=None),
  category: str | None = Query(default="all"),
  db: Session = Depends(get_db),
) -> list[schemas.LotOut]:
  stmt = select(models.Lot).options(joinedload(models.Lot.category)).join(models.Category)
  stmt = apply_lot_filters(stmt, q=q, category=category, only_available=False)
  stmt = stmt.order_by(models.Lot.sort_order.asc(), models.Lot.name.asc())
  lots = db.scalars(stmt).all()
  return [lot_to_schema(lot) for lot in lots]


@app.get("/api/v1/admin/lots/{slug}", response_model=schemas.LotOut)
def admin_get_lot(slug: str, db: Session = Depends(get_db)) -> schemas.LotOut:
  lot = lot_by_slug_or_404(db, slug)
  return lot_to_schema(lot)


@app.post("/api/v1/admin/lots", response_model=schemas.LotOut, status_code=status.HTTP_201_CREATED)
def admin_create_lot(payload: schemas.LotCreate, db: Session = Depends(get_db)) -> schemas.LotOut:
  exists = db.scalar(select(models.Lot).where(models.Lot.slug == payload.slug))
  if exists is not None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Lot slug '{payload.slug}' already exists")

  category = category_by_code_or_404(db, payload.category_code)
  lot = create_lot_model(payload, category.id)
  db.add(lot)
  db.commit()
  db.refresh(lot)
  lot = lot_by_slug_or_404(db, lot.slug)
  return lot_to_schema(lot)


@app.post("/api/v1/admin/lots/bulk", response_model=schemas.LotBulkCreateResult)
def admin_bulk_create_lots(payload: schemas.LotBulkCreate, db: Session = Depends(get_db)) -> schemas.LotBulkCreateResult:
  items = payload.items
  if not items:
    return schemas.LotBulkCreateResult(created=[], errors=[], total=0)

  categories = db.scalars(select(models.Category)).all()
  category_map = {category.code: category for category in categories}

  requested_slugs = [item.slug for item in items]
  existing_slugs = set(
    db.scalars(select(models.Lot.slug).where(models.Lot.slug.in_(requested_slugs))).all()
  )

  new_lots: list[models.Lot] = []
  errors: list[schemas.LotBulkCreateError] = []
  planned_slugs: set[str] = set()

  for item in items:
    if item.slug in existing_slugs:
      errors.append(schemas.LotBulkCreateError(slug=item.slug, reason="Slug already exists"))
      continue
    if item.slug in planned_slugs:
      errors.append(schemas.LotBulkCreateError(slug=item.slug, reason="Duplicate slug in payload"))
      continue

    category = category_map.get(item.category_code)
    if category is None:
      errors.append(
        schemas.LotBulkCreateError(slug=item.slug, reason=f"Category '{item.category_code}' not found")
      )
      continue

    lot = create_lot_model(item, category.id)
    db.add(lot)
    new_lots.append(lot)
    planned_slugs.add(item.slug)

  db.commit()

  created = [lot_to_schema(lot_by_slug_or_404(db, lot.slug)) for lot in new_lots]
  return schemas.LotBulkCreateResult(created=created, errors=errors, total=len(items))


@app.post("/api/v1/admin/lots/{slug}/duplicate", response_model=schemas.LotOut, status_code=status.HTTP_201_CREATED)
def admin_duplicate_lot(
  slug: str,
  payload: schemas.LotDuplicateCreate,
  db: Session = Depends(get_db),
) -> schemas.LotOut:
  source = lot_by_slug_or_404(db, slug)

  exists = db.scalar(select(models.Lot).where(models.Lot.slug == payload.new_slug))
  if exists is not None:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail=f"Lot slug '{payload.new_slug}' already exists",
    )

  duplicate = models.Lot(
    slug=payload.new_slug,
    name=payload.new_name or source.name,
    category_id=source.category_id,
    price=source.price,
    description=source.description,
    specs=list(source.specs or []),
    images=list(source.images or []),
    featured=source.featured if payload.featured is None else payload.featured,
    sold=False if payload.sold is None else payload.sold,
    glitch_background=source.glitch_background,
    sort_order=source.sort_order if payload.sort_order is None else payload.sort_order,
  )
  db.add(duplicate)
  db.commit()
  db.refresh(duplicate)
  fresh = lot_by_slug_or_404(db, duplicate.slug)
  return lot_to_schema(fresh)


@app.patch("/api/v1/admin/lots/{slug}", response_model=schemas.LotOut)
def admin_update_lot(slug: str, payload: schemas.LotUpdate, db: Session = Depends(get_db)) -> schemas.LotOut:
  lot = lot_by_slug_or_404(db, slug)

  data = payload.dict(exclude_unset=True)
  if "slug" in data and data["slug"] != slug:
    exists = db.scalar(select(models.Lot).where(models.Lot.slug == data["slug"]))
    if exists is not None:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Lot slug '{data['slug']}' already exists")

  if "category_code" in data:
    category = category_by_code_or_404(db, data.pop("category_code"))
    lot.category_id = category.id

  for key, value in data.items():
    setattr(lot, key, value)

  db.commit()
  db.refresh(lot)

  refreshed = lot_by_slug_or_404(db, lot.slug)
  return lot_to_schema(refreshed)


@app.delete(
  "/api/v1/admin/lots/{slug}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_class=Response,
)
def admin_delete_lot(slug: str, db: Session = Depends(get_db)):
  lot = db.scalar(select(models.Lot).where(models.Lot.slug == slug))
  if lot is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lot '{slug}' not found")
  db.delete(lot)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/v1/admin/categories", response_model=list[schemas.CategoryOut])
def admin_list_categories(db: Session = Depends(get_db)) -> list[schemas.CategoryOut]:
  categories = db.scalars(select(models.Category).order_by(models.Category.sort_order.asc())).all()
  return [schemas.CategoryOut.from_orm(category) for category in categories]


@app.post("/api/v1/admin/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def admin_create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)) -> schemas.CategoryOut:
  existing = db.scalar(select(models.Category).where(models.Category.code == payload.code))
  if existing is not None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Category '{payload.code}' already exists")

  category = models.Category(code=payload.code, label=payload.label, sort_order=payload.sort_order)
  db.add(category)
  db.commit()
  db.refresh(category)
  return schemas.CategoryOut.from_orm(category)


@app.patch("/api/v1/admin/categories/{code}", response_model=schemas.CategoryOut)
def admin_update_category(code: str, payload: schemas.CategoryUpdate, db: Session = Depends(get_db)) -> schemas.CategoryOut:
  category = category_by_code_or_404(db, code)

  data = payload.dict(exclude_unset=True)
  for key, value in data.items():
    setattr(category, key, value)

  db.commit()
  db.refresh(category)
  return schemas.CategoryOut.from_orm(category)


@app.delete(
  "/api/v1/admin/categories/{code}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_class=Response,
)
def admin_delete_category(code: str, db: Session = Depends(get_db)):
  category = category_by_code_or_404(db, code)
  in_use = db.scalar(select(func.count(models.Lot.id)).where(models.Lot.category_id == category.id))
  if in_use:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Category is used by lots. Reassign or delete lots first.",
    )

  db.delete(category)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/v1/admin/contacts", response_model=list[schemas.ContactOut])
def admin_list_contacts(db: Session = Depends(get_db)) -> list[schemas.ContactOut]:
  contacts = db.scalars(
    select(models.ContactChannel).order_by(models.ContactChannel.sort_order.asc(), models.ContactChannel.code.asc())
  ).all()
  return [schemas.ContactOut.from_orm(contact) for contact in contacts]


@app.post("/api/v1/admin/contacts", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def admin_create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db)) -> schemas.ContactOut:
  existing = db.scalar(select(models.ContactChannel).where(models.ContactChannel.code == payload.code))
  if existing is not None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Contact '{payload.code}' already exists")

  contact = models.ContactChannel(**payload.dict())
  db.add(contact)
  db.commit()
  db.refresh(contact)
  return schemas.ContactOut.from_orm(contact)


@app.patch("/api/v1/admin/contacts/{code}", response_model=schemas.ContactOut)
def admin_update_contact(code: str, payload: schemas.ContactUpdate, db: Session = Depends(get_db)) -> schemas.ContactOut:
  contact = contact_by_code_or_404(db, code)

  data = payload.dict(exclude_unset=True)
  for key, value in data.items():
    setattr(contact, key, value)

  db.commit()
  db.refresh(contact)
  return schemas.ContactOut.from_orm(contact)


@app.delete(
  "/api/v1/admin/contacts/{code}",
  status_code=status.HTTP_204_NO_CONTENT,
  response_class=Response,
)
def admin_delete_contact(code: str, db: Session = Depends(get_db)):
  contact = contact_by_code_or_404(db, code)
  db.delete(contact)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)

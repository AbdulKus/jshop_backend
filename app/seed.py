"""Database seed helpers."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"


def load_seed_data() -> dict:
  with SEED_PATH.open("r", encoding="utf-8") as seed_file:
    return json.load(seed_file)


def seed_if_empty(db: Session) -> None:
  has_lots = db.execute(select(models.Lot.id).limit(1)).first()
  if has_lots:
    return

  seed_data = load_seed_data()
  category_labels: dict[str, str] = seed_data.get("category_labels", {})

  categories: dict[str, models.Category] = {}
  sort_index = 0
  for code, label in category_labels.items():
    if code == "all":
      continue
    category = models.Category(code=code, label=label, sort_order=sort_index)
    sort_index += 1
    db.add(category)
    categories[code] = category

  for contact_data in seed_data.get("contacts", []):
    db.add(
      models.ContactChannel(
        code=contact_data.get("code", ""),
        label=contact_data.get("label", ""),
        hint=contact_data.get("hint", ""),
        url_template=contact_data.get("url_template", ""),
        subject_template=contact_data.get("subject_template", ""),
        body_template=contact_data.get("body_template", ""),
        is_external=bool(contact_data.get("is_external", True)),
        icon_svg=contact_data.get("icon_svg", ""),
        sort_order=int(contact_data.get("sort_order", 0)),
      )
    )

  db.flush()

  for lot_data in seed_data.get("lots", []):
    category_code = lot_data.get("category_code", "")
    category = categories.get(category_code)
    if not category:
      continue

    db.add(
      models.Lot(
        slug=lot_data.get("slug", ""),
        name=lot_data.get("name", ""),
        category_id=category.id,
        price=int(lot_data.get("price", 0)),
        description=lot_data.get("description", ""),
        specs=lot_data.get("specs", []),
        images=lot_data.get("images", []),
        featured=bool(lot_data.get("featured", False)),
        sold=bool(lot_data.get("sold", False)),
        glitch_background=lot_data.get("glitch_background", ""),
        sort_order=int(lot_data.get("sort_order", 0)),
      )
    )

  db.commit()

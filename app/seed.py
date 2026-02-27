"""Database seed helpers."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"

DEFAULT_SITE_TEXTS: list[dict[str, str]] = [
  {"key": "site.window_title", "value": "AeroGem Atelier", "description": "Название витрины в шапке окна"},
  {"key": "hero.kicker", "value": "Новая коллекция 2026", "description": "Кикер в шапке"},
  {"key": "hero.title", "value": "Ювелирная витрина с эффектом живого стекла", "description": "Заголовок шапки"},
  {
    "key": "hero.description",
    "value": "Воздушный Windows Aero стиль, хрустальные блики и мягкий объем. Нажимайте на лоты ниже: откроется полноценная карточка с описанием, листанием фото и детальными характеристиками.",
    "description": "Описание в шапке",
  },
  {"key": "hero.action.catalog", "value": "Смотреть лоты", "description": "Кнопка скролла к каталогу"},
  {"key": "hero.action.featured", "value": "Открыть витринный лот", "description": "Кнопка открытия витринного лота"},
  {"key": "hero.action.layout_mobile", "value": "Мобильная верстка", "description": "Текст кнопки переключения на мобильную верстку"},
  {"key": "hero.action.layout_desktop", "value": "ПК верстка", "description": "Текст кнопки переключения на ПК верстку"},
  {
    "key": "layout.phone_default_mode",
    "value": "desktop",
    "description": "Стартовый режим на телефоне: desktop или mobile",
  },
  {"key": "widget.catalog_count", "value": "Лотов в каталоге", "description": "Подпись счетчика всех лотов"},
  {"key": "widget.sold_count", "value": "Проданных лотов", "description": "Подпись счетчика проданных лотов"},
  {"key": "widget.visits_count", "value": "Количество визитов", "description": "Подпись счетчика визитов"},
  {"key": "toolbar.title", "value": "Панель подбора", "description": "Заголовок панели фильтров"},
  {"key": "toolbar.search.label", "value": "Поиск по названию", "description": "Подпись поля поиска"},
  {"key": "toolbar.search.placeholder", "value": "Например: сапфир или кольцо", "description": "Плейсхолдер поля поиска"},
  {"key": "toolbar.sort.label", "value": "Сортировка", "description": "Подпись сортировки"},
  {"key": "toolbar.sort.featured", "value": "Сначала рекомендуемые", "description": "Опция сортировки featured"},
  {"key": "toolbar.sort.price_asc", "value": "Цена: по возрастанию", "description": "Опция сортировки по цене вверх"},
  {"key": "toolbar.sort.price_desc", "value": "Цена: по убыванию", "description": "Опция сортировки по цене вниз"},
  {"key": "toolbar.sort.name_asc", "value": "Название: А-Я", "description": "Опция сортировки по названию"},
  {"key": "toolbar.available", "value": "В наличии", "description": "Лейбл фильтра наличия"},
  {"key": "toolbar.categories", "value": "Категории", "description": "Лейбл блока категорий"},
  {"key": "catalog.title", "value": "Лоты", "description": "Заголовок каталога"},
  {
    "key": "catalog.note",
    "value": "Карточки интерактивные: нажмите на любой лот для детального просмотра.",
    "description": "Подзаголовок каталога",
  },
  {
    "key": "catalog.empty",
    "value": "Ничего не найдено. Попробуйте изменить фильтр или поиск.",
    "description": "Сообщение пустого результата",
  },
  {"key": "tray.title", "value": "Трей лотов", "description": "Заголовок трея"},
  {"key": "tray.empty", "value": "Свернутые окна появятся здесь.", "description": "Пустой трей"},
  {"key": "pagination.prev", "value": "Назад", "description": "Кнопка предыдущей страницы"},
  {"key": "pagination.next", "value": "Вперед", "description": "Кнопка следующей страницы"},
  {"key": "pagination.page_aria", "value": "Страница {page}", "description": "ARIA для кнопки страницы"},
  {
    "key": "pagination.max_desktop",
    "value": "16",
    "description": "Макс. лотов на странице в ПК-режиме (автоподстройка ±4)",
  },
  {
    "key": "pagination.max_mobile",
    "value": "8",
    "description": "Макс. лотов на странице в мобильном режиме (автоподстройка ±4)",
  },
  {"key": "lot.window.title_prefix", "value": "Лот: {name}", "description": "Заголовок окна лота"},
  {"key": "lot.order.contacts", "value": "Контакты для заказа", "description": "Кнопка раскрытия контактов"},
  {"key": "lot.order.sold", "value": "Лот продан", "description": "Текст кнопки контактов для проданного лота"},
  {"key": "lot.card.open", "value": "Открыть", "description": "Кнопка открытия карточки"},
  {"key": "lot.placeholder.title", "value": "Скоро в каталоге", "description": "Заголовок плейсхолдера карточки"},
  {
    "key": "lot.placeholder.text",
    "value": "Новая ювелирная позиция\nпоявится здесь",
    "description": "Текст плейсхолдера карточки",
  },
  {"key": "lot.status.sold", "value": "Продано", "description": "Бейдж проданного лота"},
  {"key": "lot.status.sold_aria", "value": "Лот продан", "description": "ARIA для бейджа проданного лота"},
  {
    "key": "minimize.limit_hint",
    "value": "Лимит свернутых окон: {limit}",
    "description": "Подсказка лимита свернутых окон",
  },
  {"key": "lot.thumbnail.aria", "value": "Открыть фото {index}", "description": "ARIA миниатюры фото"},
  {"key": "lot.thumbnail.alt", "value": "{lot_name} миниатюра {index}", "description": "ALT миниатюры"},
  {"key": "lot.image.alt", "value": "{lot_name} - фото {index}", "description": "ALT основного фото"},
]


def load_seed_data() -> dict:
  with SEED_PATH.open("r", encoding="utf-8") as seed_file:
    return json.load(seed_file)


def ensure_site_metrics(db: Session) -> None:
  visits = db.scalar(select(models.SiteMetric).where(models.SiteMetric.key == "visits"))
  if visits is None:
    db.add(models.SiteMetric(key="visits", value=0))


def ensure_site_texts(db: Session) -> None:
  existing_keys = set(db.scalars(select(models.SiteText.key)).all())
  for item in DEFAULT_SITE_TEXTS:
    key = item["key"]
    if key in existing_keys:
      continue
    db.add(
      models.SiteText(
        key=key,
        value=item["value"],
        description=item["description"],
      )
    )


def seed_if_empty(db: Session) -> None:
  seed_data = load_seed_data()
  ensure_site_metrics(db)
  ensure_site_texts(db)

  has_lots = db.execute(select(models.Lot.id).limit(1)).first()
  if has_lots:
    db.commit()
    return

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

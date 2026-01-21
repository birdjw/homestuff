from collections import defaultdict
from typing import Dict, List

from ..extensions import db
from ..models import Item, RestockEntry, StorageArea, Vendor
from sqlalchemy import or_, and_


def _vendor_name(item_vendor, area_vendor):
    return (item_vendor or area_vendor or Vendor(name="Unspecified")).name


def _serialize_item(item: Item) -> Dict:
    vendor_name = _vendor_name(item.vendor, item.storage_area.vendor)
    return {
        "type": "item",
        "id": item.id,
        "name": item.name,
        "storage_area": item.storage_area.name,
        "vendor_name": vendor_name,
        "on_hand": item.on_hand,
        "minimum_quantity": item.minimum_quantity,
        "below_minimum": item.is_below_minimum,
    }


def _serialize_manual(entry: RestockEntry) -> Dict:
    vendor_name = entry.vendor.name if entry.vendor else None
    storage_area_name = entry.storage_area.name if entry.storage_area else None
    return {
        "type": "manual",
        "id": entry.id,
        "name": entry.name,
        "storage_area": storage_area_name,
        "vendor_name": vendor_name or "Unspecified",
        "reason": entry.reason,
    }


def build_restock_snapshot(user_id: int) -> Dict[str, List[Dict]]:
    # Items tracked by quantity below minimum OR items tracked as binary and marked low
    auto_items = Item.query.filter(
        Item.user_id == user_id,
        or_(
            and_(Item.tracking_method == 'quantity', Item.on_hand < Item.minimum_quantity),
            and_(Item.tracking_method == 'binary', Item.is_low == True),
        ),
    ).all()
    manual_entries = RestockEntry.query.filter_by(user_id=user_id, is_resolved=False).all()

    auto_payload = [_serialize_item(item) for item in auto_items]
    manual_payload = [_serialize_manual(entry) for entry in manual_entries]

    combined = auto_payload + manual_payload
    shopping_by_vendor = defaultdict(list)
    for entry in combined:
        vendor_key = entry.get("vendor_name") or "Unspecified"
        shopping_by_vendor[vendor_key].append(entry)

    return {
        "auto": auto_payload,
        "manual": manual_payload,
        "shopping_by_vendor": dict(shopping_by_vendor),
    }


def add_manual_restock(name: str, user_id: int, vendor_id=None, storage_area_id=None, reason: str | None = None):
    vendor = Vendor.query.filter_by(id=vendor_id, user_id=user_id).first() if vendor_id else None
    storage_area = StorageArea.query.filter_by(id=storage_area_id, user_id=user_id).first() if storage_area_id else None
    entry = RestockEntry(
        name=name,
        vendor=vendor,
        storage_area=storage_area,
        is_manual=True,
        reason=reason,
        user_id=user_id,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def resolve_manual_entry(entry: RestockEntry):
    entry.is_resolved = True
    db.session.commit()
    return entry

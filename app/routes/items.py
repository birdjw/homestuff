from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from sqlalchemy.exc import SQLAlchemyError
from ..models import Item, StorageArea, Vendor

bp = Blueprint("items", __name__, url_prefix="/items")


def _item_to_dict(item: Item):
    return {
        "id": item.id,
        "name": item.name,
        "tracking_method": item.tracking_method,
        "is_low": bool(item.is_low),
        "storage_area_id": item.storage_area_id,
        "storage_area_name": item.storage_area.name if item.storage_area else None,
        "vendor_id": item.vendor_id,
        "vendor_name": item.vendor.name if item.vendor else None,
        "minimum_quantity": item.minimum_quantity,
        "on_hand": item.on_hand,
        "below_minimum": item.is_below_minimum,
    }


@bp.get("")
@login_required
def list_items():
    storage_area_id = request.args.get("storage_area_id", type=int)
    query = Item.query.filter_by(user_id=current_user.id)
    if storage_area_id:
        query = query.filter_by(storage_area_id=storage_area_id)
    items = query.order_by(Item.name.asc()).all()
    return jsonify([_item_to_dict(item) for item in items])


@bp.post("")
@login_required
def create_item():
    payload = request.get_json() or {}
    name = payload.get("name")
    storage_area_id = payload.get("storage_area_id")
    if not name or not storage_area_id:
        return jsonify({"error": "name and storage_area_id are required"}), 400

    storage_area = StorageArea.query.filter_by(id=storage_area_id, user_id=current_user.id).first()
    if not storage_area:
        return jsonify({"error": "storage_area not found"}), 404

    vendor_id = payload.get("vendor_id")
    if vendor_id:
        vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first()
        if not vendor:
            return jsonify({"error": "vendor not found"}), 404
    else:
        vendor = None

    # determine low flag and enforce binary tracking if low is set
    is_low = bool(payload.get("is_low", False))
    tracking_method = "binary" if is_low else payload.get("tracking_method", "quantity")
    item = Item(
        name=name,
        storage_area=storage_area,
        vendor=vendor,
        is_low=is_low,
        tracking_method=tracking_method,
        minimum_quantity=(None if tracking_method == 'binary' else max(int(payload.get("minimum_quantity", 0)), 0)),
        on_hand=(None if tracking_method == 'binary' else max(int(payload.get("on_hand", 0)), 0)),
        user_id=current_user.id,
    )
    db.session.add(item)
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    return jsonify(_item_to_dict(item)), 201


@bp.get("/<int:item_id>")
@login_required
def get_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    return jsonify(_item_to_dict(item))


@bp.patch("/<int:item_id>")
@login_required
def update_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    payload = request.get_json() or {}

    if "name" in payload:
        item.name = payload["name"]
    if "minimum_quantity" in payload:
        # ignore minimum for binary-tracked items
        if item.tracking_method == 'binary':
            item.minimum_quantity = None
        else:
            item.minimum_quantity = max(int(payload.get("minimum_quantity", 0)), 0)
    if "on_hand" in payload:
        # ignore on_hand for binary-tracked items
        if item.tracking_method == 'binary':
            item.on_hand = None
        else:
            item.on_hand = max(int(payload.get("on_hand", 0)), 0)
    if "storage_area_id" in payload:
        storage_area = StorageArea.query.filter_by(id=payload.get("storage_area_id"), user_id=current_user.id).first()
        if not storage_area:
            return jsonify({"error": "storage_area not found"}), 404
        item.storage_area = storage_area
    if "tracking_method" in payload:
        tm = payload.get("tracking_method")
        if tm in ("quantity", "binary"):
            item.tracking_method = tm
            # when switching tracking mode, adjust numeric fields accordingly
            if tm == 'binary':
                item.minimum_quantity = None
                item.on_hand = None
            else:
                # ensure numeric fields are present for quantity tracking
                if item.minimum_quantity is None:
                    item.minimum_quantity = 0
                if item.on_hand is None:
                    item.on_hand = 0
        else:
            return jsonify({"error": "invalid tracking_method"}), 400
    if "is_low" in payload:
        item.is_low = bool(payload.get("is_low"))
        if item.is_low:
            item.tracking_method = "binary"
    if "vendor_id" in payload:
        vendor_id = payload.get("vendor_id")
        if vendor_id:
            vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first()
            if not vendor:
                return jsonify({"error": "vendor not found"}), 404
            item.vendor = vendor
        else:
            item.vendor = None

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    return jsonify(_item_to_dict(item))


@bp.post("/<int:item_id>/adjust")
@login_required
def adjust_item_quantity(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    payload = request.get_json() or {}
    delta = payload.get("delta")
    if delta is None:
        return jsonify({"error": "delta is required"}), 400

    item.adjust_quantity(int(delta))
    db.session.commit()
    return jsonify(_item_to_dict(item))


@bp.delete("/<int:item_id>")
@login_required
def delete_item(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "deleted", "id": item_id})

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from ..models import StorageArea, Vendor

bp = Blueprint("storage_areas", __name__, url_prefix="/storage-areas")


def _area_to_dict(area: StorageArea):
    return {
        "id": area.id,
        "name": area.name,
        "vendor_id": area.vendor_id,
        "vendor_name": area.vendor.name if area.vendor else None,
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "minimum_quantity": item.minimum_quantity,
                "on_hand": item.on_hand,
                "vendor_id": item.vendor_id,
            }
            for item in area.items
        ],
    }


@bp.get("")
@login_required
def list_storage_areas():
    areas = StorageArea.query.filter_by(user_id=current_user.id).order_by(StorageArea.name.asc()).all()
    return jsonify([_area_to_dict(area) for area in areas])


@bp.post("")
@login_required
def create_storage_area():
    payload = request.get_json() or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    vendor_id = payload.get("vendor_id")
    vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first() if vendor_id else None
    area = StorageArea(name=name, vendor=vendor, user_id=current_user.id)
    db.session.add(area)
    db.session.commit()
    return jsonify(_area_to_dict(area)), 201


@bp.get("/<int:area_id>")
@login_required
def get_storage_area(area_id):
    area = StorageArea.query.filter_by(id=area_id, user_id=current_user.id).first_or_404()
    return jsonify(_area_to_dict(area))


@bp.patch("/<int:area_id>")
@login_required
def update_storage_area(area_id):
    area = StorageArea.query.filter_by(id=area_id, user_id=current_user.id).first_or_404()
    payload = request.get_json() or {}

    if "name" in payload:
        area.name = payload["name"]
    if "vendor_id" in payload:
        vendor_id = payload.get("vendor_id")
        area.vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first() if vendor_id else None

    db.session.commit()
    return jsonify(_area_to_dict(area))


@bp.delete("/<int:area_id>")
@login_required
def delete_storage_area(area_id):
    area = StorageArea.query.filter_by(id=area_id, user_id=current_user.id).first_or_404()
    db.session.delete(area)
    db.session.commit()
    return jsonify({"status": "deleted", "id": area_id})

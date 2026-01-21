from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from ..models import RestockEntry, StorageArea, Vendor
from ..services.restock_service import add_manual_restock, build_restock_snapshot, resolve_manual_entry

bp = Blueprint("restock", __name__, url_prefix="/restock")


@bp.get("")
@login_required
def restock_list():
    try:
        payload = build_restock_snapshot(current_user.id)
    except Exception as exc:
        from flask import current_app

        current_app.logger.exception("Error building restock snapshot")
        return (
            jsonify({"error": "database_unavailable", "message": str(exc)}),
            503,
        )

    return jsonify(payload)


@bp.post("/manual")
@login_required
def create_manual_entry():
    payload = request.get_json() or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    vendor_id = payload.get("vendor_id")
    if vendor_id:
        vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first()
        if not vendor:
            return jsonify({"error": "vendor not found"}), 404

    storage_area_id = payload.get("storage_area_id")
    if storage_area_id:
        storage_area = StorageArea.query.filter_by(id=storage_area_id, user_id=current_user.id).first()
        if not storage_area:
            return jsonify({"error": "storage area not found"}), 404

    entry = add_manual_restock(
        name=name,
        vendor_id=vendor_id,
        storage_area_id=storage_area_id,
        reason=payload.get("reason"),
        user_id=current_user.id,
    )
    return jsonify({"id": entry.id, "name": entry.name, "is_manual": entry.is_manual}), 201


@bp.post("/<int:entry_id>/resolve")
@login_required
def resolve_entry(entry_id):
    entry = RestockEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    if not entry.is_manual:
        return jsonify({"error": "Only manual entries can be resolved here."}), 400

    resolve_manual_entry(entry)
    return jsonify({"status": "resolved", "id": entry.id})


@bp.delete("/<int:entry_id>")
@login_required
def delete_manual_entry(entry_id):
    entry = RestockEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    if not entry.is_manual:
        return jsonify({"error": "Only manual entries can be deleted here."}), 400

    db.session.delete(entry)
    db.session.commit()
    return jsonify({"status": "deleted", "id": entry_id})

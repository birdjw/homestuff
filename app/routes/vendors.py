from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Vendor

bp = Blueprint("vendors", __name__, url_prefix="/vendors")


def _vendor_to_dict(vendor: Vendor):
    return {"id": vendor.id, "name": vendor.name}


@bp.get("")
@login_required
def list_vendors():
    vendors = Vendor.query.filter_by(user_id=current_user.id).order_by(Vendor.name.asc()).all()
    return jsonify([_vendor_to_dict(vendor) for vendor in vendors])


@bp.post("")
@login_required
def create_vendor():
    payload = request.get_json() or {}
    name = payload.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400

    vendor = Vendor(name=name, user_id=current_user.id)
    db.session.add(vendor)
    db.session.commit()
    return jsonify(_vendor_to_dict(vendor)), 201


@bp.patch("/<int:vendor_id>")
@login_required
def update_vendor(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first_or_404()
    payload = request.get_json() or {}
    if "name" in payload:
        vendor.name = payload["name"]
    db.session.commit()
    return jsonify(_vendor_to_dict(vendor))


@bp.delete("/<int:vendor_id>")
@login_required
def delete_vendor(vendor_id):
    vendor = Vendor.query.filter_by(id=vendor_id, user_id=current_user.id).first_or_404()
    db.session.delete(vendor)
    db.session.commit()
    return jsonify({"status": "deleted", "id": vendor_id})

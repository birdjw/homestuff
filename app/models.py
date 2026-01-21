from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Relationships
    vendors = db.relationship("Vendor", back_populates="user", cascade="all, delete-orphan", lazy=True)
    storage_areas = db.relationship("StorageArea", back_populates="user", cascade="all, delete-orphan", lazy=True)
    items = db.relationship("Item", back_populates="user", cascade="all, delete-orphan", lazy=True)
    restock_entries = db.relationship("RestockEntry", back_populates="user", cascade="all, delete-orphan", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Vendor(TimestampMixin, db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="vendors")
    storage_areas = db.relationship("StorageArea", back_populates="vendor", lazy=True)
    items = db.relationship("Item", back_populates="vendor", lazy=True)
    restock_entries = db.relationship("RestockEntry", back_populates="vendor", lazy=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_vendor_uc'),)

    def __repr__(self):
        return f"<Vendor {self.name}>"


class StorageArea(TimestampMixin, db.Model):
    __tablename__ = "storage_areas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)

    user = db.relationship("User", back_populates="storage_areas")
    vendor = db.relationship("Vendor", back_populates="storage_areas")
    items = db.relationship("Item", back_populates="storage_area", cascade="all, delete")
    restock_entries = db.relationship(
        "RestockEntry", back_populates="storage_area", cascade="all, delete"
    )

    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_area_uc'),)

    def __repr__(self):
        return f"<StorageArea {self.name}>"


class Item(TimestampMixin, db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    # tracking_method: 'quantity' (default) or 'binary' (low flag)
    tracking_method = db.Column(db.String(32), nullable=False, default='quantity')
    # when tracking_method == 'binary', this flag indicates the item is low
    is_low = db.Column(db.Boolean, default=False, nullable=False)
    storage_area_id = db.Column(db.Integer, db.ForeignKey("storage_areas.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    minimum_quantity = db.Column(db.Integer, default=0, nullable=False)
    on_hand = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="items")
    storage_area = db.relationship("StorageArea", back_populates="items")
    vendor = db.relationship("Vendor", back_populates="items")
    restock_entries = db.relationship("RestockEntry", back_populates="item")

    @property
    def is_below_minimum(self) -> bool:
        if self.tracking_method == 'binary':
            return bool(self.is_low)
        return self.on_hand < self.minimum_quantity

    def adjust_quantity(self, delta: int):
        new_value = self.on_hand + delta
        self.on_hand = max(new_value, 0)

    def __repr__(self):
        return f"<Item {self.name} ({self.on_hand}/{self.minimum_quantity})>"


class RestockEntry(TimestampMixin, db.Model):
    __tablename__ = "restock_entries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)
    storage_area_id = db.Column(db.Integer, db.ForeignKey("storage_areas.id"), nullable=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=True)
    is_manual = db.Column(db.Boolean, default=True, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.String(200), nullable=True)

    user = db.relationship("User", back_populates="restock_entries")
    item = db.relationship("Item", back_populates="restock_entries")
    storage_area = db.relationship("StorageArea", back_populates="restock_entries")
    vendor = db.relationship("Vendor", back_populates="restock_entries")

    def __repr__(self):
        return f"<RestockEntry {self.name} manual={self.is_manual} resolved={self.is_resolved}>"

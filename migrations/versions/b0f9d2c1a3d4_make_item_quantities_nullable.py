"""make item quantities nullable

Revision ID: b0f9d2c1a3d4
Revises: 7400f89d7aa4
Create Date: 2026-01-22 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0f9d2c1a3d4'
down_revision = '7400f89d7aa4'
branch_labels = None
depends_on = None


def upgrade():
    # Make minimum_quantity and on_hand nullable to support binary-tracked items
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.alter_column('minimum_quantity', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('on_hand', existing_type=sa.Integer(), nullable=True)


def downgrade():
    # Ensure no NULLs exist before making columns NOT NULL
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE items SET minimum_quantity = 0 WHERE minimum_quantity IS NULL"))
    conn.execute(sa.text("UPDATE items SET on_hand = 0 WHERE on_hand IS NULL"))

    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.alter_column('minimum_quantity', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('on_hand', existing_type=sa.Integer(), nullable=False)

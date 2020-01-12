"""add devices table

Revision ID: 07f2680e4b64
Revises:
Create Date: 2020-01-12 12:08:10.676469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07f2680e4b64'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer, primary_key=True, comment='Generated device ID'),
        sa.Column('model', sa.String(100), nullable=False, comment='Model ID used for lookup with vendor'),
        sa.Column('vendor_id', sa.String(30), nullable=False, comment='Vendor ID corresponding with the vendor module for lookup within homenet'),
        sa.Column('version', sa.String(80), comment='Device current known version'),
        sa.Column('description', sa.String(255), comment='Meaningful description (like "Home router")')
    )


def downgrade():
    op.drop_table('devices')

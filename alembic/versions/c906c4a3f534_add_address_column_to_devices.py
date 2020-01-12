"""add address column to devices

Revision ID: c906c4a3f534
Revises: 07f2680e4b64
Create Date: 2020-01-12 12:08:19.560564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c906c4a3f534'
down_revision = '07f2680e4b64'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('devices', sa.Column('address', sa.String(255), comment='Network address for management console (e.g. IP or Web Address)'))


def downgrade():
    # Use batch operation for drop column as SQLite does not natively support it
    # See https://alembic.sqlalchemy.org/en/latest/batch.html
    # op.drop_column('devices', 'address')
    with op.batch_alter_table('devices') as batch_op:
        batch_op.drop_column('address')
    

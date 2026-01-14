"""add decision fields to contract_updates

Revision ID: 006_add_update_decision_fields
Revises: 005_merge_heads
Create Date: 2026-01-14

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
# NOTE: alembic_version.version_num is VARCHAR(32) in this project, so keep revision ids <= 32 chars.
revision = "006_add_update_decision_fields"
down_revision = "005_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contract_updates", sa.Column("decision", sa.String(length=50), nullable=True))
    op.add_column("contract_updates", sa.Column("decision_comments", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("contract_updates", "decision_comments")
    op.drop_column("contract_updates", "decision")


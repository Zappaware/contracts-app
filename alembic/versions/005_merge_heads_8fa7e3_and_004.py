"""merge heads 8fa7e3baf38b and 004_add_owner_role

Revision ID: 005_merge_heads
Revises: 8fa7e3baf38b, 004_add_owner_role
Create Date: 2026-01-14

"""

from alembic import op


# revision identifiers, used by Alembic.
# NOTE: alembic_version.version_num is VARCHAR(32) in this project, so keep revision ids <= 32 chars.
revision = "005_merge_heads"
down_revision = ("8fa7e3baf38b", "004_add_owner_role")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge-only migration (no schema changes)."""
    pass


def downgrade() -> None:
    """Merge-only migration (no schema changes)."""
    pass


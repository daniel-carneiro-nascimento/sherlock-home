"""add opaque public ids to config resources

Revision ID: fa124f53f7f3
Revises: fb31311b521c
Create Date: 2026-09-03 00:29:48.891437

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fa124f53f7f3"
down_revision: Union[str, Sequence[str], None] = "fb31311b521c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add opaque public IDs to configuration resources."""

    op.add_column(
        "category_rules",
        sa.Column(
            "public_id",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "merchant_aliases",
        sa.Column(
            "public_id",
            sa.String(length=64),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    category_rows = connection.execute(
        sa.text(
            "SELECT id "
            "FROM category_rules "
            "WHERE public_id IS NULL"
        )
    ).fetchall()

    for row in category_rows:
        connection.execute(
            sa.text(
                "UPDATE category_rules "
                "SET public_id = :public_id "
                "WHERE id = :id"
            ),
            {
                "public_id": f"cr_{uuid.uuid4().hex}",
                "id": row.id,
            },
        )

    merchant_rows = connection.execute(
        sa.text(
            "SELECT id "
            "FROM merchant_aliases "
            "WHERE public_id IS NULL"
        )
    ).fetchall()

    for row in merchant_rows:
        connection.execute(
            sa.text(
                "UPDATE merchant_aliases "
                "SET public_id = :public_id "
                "WHERE id = :id"
            ),
            {
                "public_id": f"ma_{uuid.uuid4().hex}",
                "id": row.id,
            },
        )

    op.alter_column(
        "category_rules",
        "public_id",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    op.alter_column(
        "merchant_aliases",
        "public_id",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    op.create_index(
        "ix_category_rules_public_id",
        "category_rules",
        ["public_id"],
        unique=True,
    )

    op.create_index(
        "ix_merchant_aliases_public_id",
        "merchant_aliases",
        ["public_id"],
        unique=True,
    )


def downgrade() -> None:
    """Remove opaque public IDs from configuration resources."""

    op.drop_index(
        "ix_merchant_aliases_public_id",
        table_name="merchant_aliases",
    )

    op.drop_index(
        "ix_category_rules_public_id",
        table_name="category_rules",
    )

    op.drop_column(
        "merchant_aliases",
        "public_id",
    )

    op.drop_column(
        "category_rules",
        "public_id",
    )
 

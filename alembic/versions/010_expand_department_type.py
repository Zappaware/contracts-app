"""expand departmenttype enum to QA bank department list

Revision ID: 010_expand_department
Revises: 009_add_draft_status
Create Date: 2026-03-24

- PostgreSQL: ALTER TYPE departmenttype ADD VALUE for each new label.
- MSSQL (and other DBs using sa.Enum string + CHECK from 001): drop restrictive
  CHECK constraints on department and widen columns before data UPDATEs.

Migrates legacy string values on contracts/users on all supported backends.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010_expand_department"
down_revision = "009_add_draft_status"
branch_labels = None
depends_on = None

# Longest QA labels are ~36 chars; leave headroom for future edits.
_DEPARTMENT_VARCHAR_LENGTH = 128

# Labels not already present on initial departmenttype (001_initial_schema).
_DEPARTMENT_TYPE_NEW_LABELS = [
    "IT - Operations",
    "Compliance Department",
    "Internal Audit",
    "Executive Office",
    "Insurance Department",
    "Premises & Facilities",
    "Marketing Department",
    "Payment Operations",
    "Payment Strategy & Solutions",
    "CARC",
    "Corporate Banking - Mid Office",
    "Security Department",
    "Management Team",
    "Special Assets",
    "Contact Center",
    "Corporate Banking - Corporate Credit",
    "Credit Risk",
    "Archiving Services",
    "Project Management Team",
    "IT - Projects",
    "KYC Due Diligence",
    "PBIO",
    "ORCO Group N.V.",
    "Business Continuity Management",
    "Management Board",
    "Integrity",
    "Platinum Banking",
    "OBAB IT",
    "OBAB Security",
    "OBAB Retail",
    "OBAB PBIO",
    "OBAB Payment Strategy & Solutions",
    "OBAB Payment Operations",
    "OBAB Premises & Facilities",
    "OBAB Internal Audit",
]


def _migrate_department_strings(bind):
    """Map legacy department strings to new catalog."""
    mapping = [
        ("IT", "IT - Operations"),
        ("Operations", "IT - Operations"),
        ("Legal", "Management Team"),
        ("Marketing", "Marketing Department"),
        ("Sales", "Contact Center"),
        ("Customer Service", "Contact Center"),
        ("Risk Management", "Credit Risk"),
        ("Compliance", "Compliance Department"),
        ("Audit", "Internal Audit"),
        ("Treasury", "Payment Operations"),
        ("Credit", "Credit Risk"),
        ("Corporate Banking", "Corporate Banking - Mid Office"),
    ]
    for table in ("contracts", "users"):
        try:
            insp = inspect(bind)
            if table not in insp.get_table_names():
                continue
        except Exception:
            continue
        for old, new in mapping:
            bind.execute(
                sa.text(f"UPDATE {table} SET department = :new WHERE department = :old"),
                {"old": old, "new": new},
            )


def _drop_enum_style_check_on_department():
    """Reflect and drop sa.Enum-style CHECKs on department (SQLite, MSSQL fallback, etc.)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    for table_name in ("users", "contracts"):
        if table_name not in inspector.get_table_names():
            continue
        for ck in inspector.get_check_constraints(table_name):
            name = ck.get("name")
            if not name:
                continue
            parts = [
                str(ck.get("sqltext") or ""),
                str(ck.get("definition") or ""),
            ]
            combined = " ".join(parts).lower()
            if "department" not in combined:
                continue
            enum_like = (
                " in " in combined
                or " in(" in combined
                or (
                    "=" in combined
                    and " or " in combined
                    and "department" in combined
                )
            )
            if not enum_like:
                continue
            try:
                op.drop_constraint(name, table_name, type_="check")
            except Exception:
                pass


def _mssql_bracket_ident(ident: str) -> str:
    """Bracket-quote a single SQL Server identifier (supports ] escaping)."""
    return "[" + ident.replace("]", "]]") + "]"


def _mssql_relax_department_columns(bind):
    """Remove SQLAlchemy Enum CHECK constraints and widen department (NVARCHAR)."""
    # sys.check_constraints.definition lists allowed enum values; it blocks new labels.
    drop_checks = sa.text(
        """
        DECLARE @sql NVARCHAR(MAX) = N'';

        SELECT @sql = @sql + N'ALTER TABLE '
            + QUOTENAME(SCHEMA_NAME(t.schema_id)) + N'.' + QUOTENAME(t.name)
            + N' DROP CONSTRAINT ' + QUOTENAME(cc.name) + N';' + CHAR(13)
        FROM sys.check_constraints AS cc
        INNER JOIN sys.tables AS t ON cc.parent_object_id = t.object_id
        WHERE t.name IN (N'users', N'contracts')
          AND cc.definition LIKE N'%department%'
          AND (
            cc.definition COLLATE Latin1_General_CI_AI LIKE N'%IN %'
            OR cc.definition COLLATE Latin1_General_CI_AI LIKE N'%IN(%'
            OR (
                cc.definition COLLATE Latin1_General_CI_AI LIKE N'%=%'
                AND cc.definition COLLATE Latin1_General_CI_AI LIKE N'%OR%'
            )
          );

        IF @sql IS NOT NULL AND LEN(@sql) > 0
            EXEC sp_executesql @sql;
        """
    )
    bind.execute(drop_checks)
    # Reflected CHECKs (covers DDL shapes sys.check_constraints does not match).
    _drop_enum_style_check_on_department()

    rows = bind.execute(
        sa.text(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_NAME IN ('users', 'contracts')"
        )
    ).fetchall()
    n = int(_DEPARTMENT_VARCHAR_LENGTH)
    for schema, table_name in rows:
        sch = schema or "dbo"
        qual = f"{_mssql_bracket_ident(sch)}.{_mssql_bracket_ident(table_name)}"
        bind.execute(
            sa.text(f"ALTER TABLE {qual} ALTER COLUMN department NVARCHAR({n}) NOT NULL")
        )


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        for label in _DEPARTMENT_TYPE_NEW_LABELS:
            escaped = label.replace("'", "''")
            op.execute(f"ALTER TYPE departmenttype ADD VALUE '{escaped}'")
    elif dialect_name == "mssql":
        _mssql_relax_department_columns(bind)
    else:
        # SQLite and other non-PG: reflected CHECK from sa.Enum(001), if present.
        _drop_enum_style_check_on_department()

    _migrate_department_strings(bind)


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely; MSSQL column type is not reverted.
    pass

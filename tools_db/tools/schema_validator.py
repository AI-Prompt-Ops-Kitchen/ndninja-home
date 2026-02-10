import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    table_name: Optional[str]
    warnings: List[str]
    errors: List[str]
    suggestions: List[str]

    def to_dict(self):
        return {
            "valid": self.valid,
            "table_name": self.table_name,
            "warnings": self.warnings,
            "errors": self.errors,
            "suggestions": self.suggestions
        }


class SchemaValidator:
    """Validate SQL schema statements before execution"""

    # PostgreSQL type mappings
    POSTGRES_TYPES = {
        'SERIAL', 'BIGSERIAL', 'SMALLINT', 'INTEGER', 'BIGINT',
        'DECIMAL', 'NUMERIC', 'REAL', 'DOUBLE PRECISION',
        'VARCHAR', 'CHAR', 'TEXT', 'BOOLEAN', 'DATE', 'TIME',
        'TIMESTAMP', 'INTERVAL', 'UUID', 'JSON', 'JSONB',
        'BYTEA', 'INET', 'CIDR', 'MACADDR', 'ARRAY'
    }

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.db = None
        if not test_mode:
            try:
                from tools_db.database import get_db
                self.db = get_db()
            except:
                pass

    def validate_create_statement(self, sql: str) -> Dict[str, Any]:
        """Validate CREATE TABLE statement"""
        warnings = []
        errors = []
        suggestions = []
        table_name = None

        try:
            # Extract table name
            match = re.search(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)', sql, re.IGNORECASE)
            if not match:
                errors.append("Could not parse table name from CREATE TABLE statement")
                return ValidationResult(False, None, warnings, errors, suggestions).to_dict()

            table_name = match.group(1)

            # Check for column definitions
            if 'PRIMARY KEY' not in sql.upper():
                warnings.append(f"Table '{table_name}' has no PRIMARY KEY - consider adding one")
                suggestions.append(f"ADD: id SERIAL PRIMARY KEY")

            # Validate column types - look for columns after table name
            # Extract the part between ( and )
            match_content = re.search(r'CREATE TABLE\s+\w+\s*\((.*)\)', sql, re.IGNORECASE | re.DOTALL)
            if match_content:
                content = match_content.group(1)
                # Split by comma and look for type definitions
                lines = content.split(',')
                for line in lines:
                    line = line.strip()
                    if not line or line.upper().startswith('CONSTRAINT'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        col_name = parts[0]
                        col_type = parts[1]
                        base_type = col_type.split('(')[0].upper().strip()
                        if base_type not in self.POSTGRES_TYPES:
                            errors.append(f"Column '{col_name}': Unknown type '{col_type}'")

            # Check for foreign key references
            fk_pattern = r'REFERENCES\s+(\w+)\((\w+)\)'
            for fk_table, fk_col in re.findall(fk_pattern, sql, re.IGNORECASE):
                if not self.test_mode:
                    # In test mode, skip database checks
                    if not self._table_exists(fk_table):
                        warnings.append(f"Referenced table '{fk_table}' may not exist yet")

            valid = len(errors) == 0
            return ValidationResult(
                valid=valid,
                table_name=table_name,
                warnings=warnings,
                errors=errors,
                suggestions=suggestions
            ).to_dict()

        except Exception as e:
            errors.append(f"Error parsing SQL: {str(e)}")
            return ValidationResult(False, table_name, warnings, errors, suggestions).to_dict()

    def validate_alter_statement(self, sql: str) -> Dict[str, Any]:
        """Validate ALTER TABLE statement"""
        warnings = []
        errors = []
        suggestions = []

        match = re.search(r'ALTER TABLE\s+(\w+)', sql, re.IGNORECASE)
        if not match:
            errors.append("Could not parse table name from ALTER TABLE")
            return {"valid": False, "warnings": warnings, "errors": errors}

        table_name = match.group(1)

        if not self.test_mode and not self._table_exists(table_name):
            errors.append(f"Table '{table_name}' does not exist")

        return {
            "valid": len(errors) == 0,
            "table_name": table_name,
            "warnings": warnings,
            "errors": errors,
            "suggestions": suggestions
        }

    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        if self.test_mode:
            return True

        try:
            if self.db is None:
                return False

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = %s
                    )
                """, (table_name,))
                return cursor.fetchone()[0]
        except:
            return False

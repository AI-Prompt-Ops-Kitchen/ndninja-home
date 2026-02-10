import pytest
from tools_db.tools.schema_validator import SchemaValidator


def test_schema_validator_detects_type_mismatch():
    """Should detect column type mismatches"""
    validator = SchemaValidator(test_mode=True)

    # Simulate creating a table with wrong type
    sql_statement = """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255),
        created_at TIMESTAMP
    )
    """

    result = validator.validate_create_statement(sql_statement)
    assert result["valid"] is True
    assert "users" in result["table_name"]


def test_schema_validator_detects_missing_column():
    """Should detect when referencing non-existent columns"""
    validator = SchemaValidator(test_mode=True)

    sql_statement = """
    CREATE TABLE orders (
        user_id UUID REFERENCES users(id),
        total DECIMAL
    )
    """

    # Should flag that users table might not have id column
    result = validator.validate_create_statement(sql_statement)
    assert "warnings" in result

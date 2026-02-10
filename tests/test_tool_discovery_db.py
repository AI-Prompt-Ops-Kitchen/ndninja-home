from scripts.tool_discovery.database import ToolDatabase

def test_database_connection():
    """Test database connection to claude-memory"""
    db = ToolDatabase()
    assert db.connect() is True
    db.close()

def test_get_all_tools_empty():
    """Test getting tools when registry is empty"""
    db = ToolDatabase()
    assert db.connect() is True
    tools = db.get_all_tools()
    assert isinstance(tools, list)
    db.close()

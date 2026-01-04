"""Configuration and constants for documentation generator"""
import os

class Config:
    """Central configuration for documentation generator"""

    # API Keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

    # Database Configurations
    WORKSPACE_DB = {
        'host': 'localhost',
        'port': 5432,
        'database': 'workspace',
        'user': 'postgres',
        'password': ''  # Using peer authentication
    }

    CLAUDE_MEMORY_DB = {
        'host': 'localhost',
        'port': 5432,
        'database': 'claude_memory',
        'user': 'claude_mcp',
        'password': 'memory123'
    }

    # Craft MCP Configuration
    CRAFT_MCP_URL = "https://mcp.craft.do/links/31NLayAJdLR/mcp"

    # Claude API Settings
    CLAUDE_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 8000
    TEMPERATURE = 0.7

    # Paths
    DOCS_OUTPUT_DIR = "/home/ndninja/docs"
    PROJECTS_DIR = "/home/ndninja/projects"

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

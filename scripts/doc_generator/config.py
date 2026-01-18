"""Configuration and constants for documentation generator"""
import os

class Config:
    """Central configuration for documentation generator"""

    # API Keys
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY', '')

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

    # Perplexity API Settings
    PERPLEXITY_MODEL = os.environ.get('PERPLEXITY_MODEL', 'sonar-pro')
    PERPLEXITY_TIMEOUT = int(os.environ.get('PERPLEXITY_TIMEOUT_MS', '60000')) / 1000
    PERPLEXITY_MAX_RETRIES = int(os.environ.get('PERPLEXITY_MAX_RETRIES', '3'))
    PERPLEXITY_ENABLED = bool(PERPLEXITY_API_KEY)

    # Paths
    DOCS_OUTPUT_DIR = "/home/ndninja/docs"
    PROJECTS_DIR = "/home/ndninja/projects"

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

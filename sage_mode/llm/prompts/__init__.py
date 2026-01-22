"""Prompt loading and assembly utilities.

Loads role-specific prompts and assembles complete prompts for LLM calls.
"""

import json
from pathlib import Path
from typing import Dict, Any, Type
from pydantic import BaseModel


# Directory containing prompt files
PROMPTS_DIR = Path(__file__).parent


# Role name mapping to prompt files
ROLE_PROMPTS = {
    "software_architect": "architect.txt",
    "backend_developer": "backend.txt",
    "frontend_developer": "frontend.txt",
    "security_specialist": "security.txt",
    "database_administrator": "dba.txt",
    "ui_ux_designer": "uiux.txt",
    "it_administrator": "itadmin.txt",
}


def load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts directory."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text().strip()


def get_base_prompt() -> str:
    """Load the base prompt template."""
    return load_prompt("base.txt")


def get_role_prompt(role: str) -> str:
    """Load the role-specific prompt for a given agent role."""
    filename = ROLE_PROMPTS.get(role)
    if not filename:
        raise ValueError(f"Unknown role: {role}. Valid roles: {list(ROLE_PROMPTS.keys())}")
    return load_prompt(filename)


def build_full_prompt(
    role: str,
    role_name: str,
    feature_name: str,
    task_description: str,
    context: Dict[str, Any],
    schema: Type[BaseModel],
) -> str:
    """Build a complete prompt for an LLM call.

    Args:
        role: Agent role key (e.g., "software_architect")
        role_name: Human-readable role name (e.g., "Software Architect")
        feature_name: Name of the feature being worked on
        task_description: What the agent should do
        context: Context from other agents or the session
        schema: Pydantic model class for the expected response

    Returns:
        Complete prompt string ready for LLM
    """
    # Load templates
    base_template = get_base_prompt()
    role_prompt = get_role_prompt(role)

    # Generate JSON schema from Pydantic model
    schema_json = json.dumps(schema.model_json_schema(), indent=2)

    # Format context as JSON
    context_json = json.dumps(context, indent=2) if context else "{}"

    # Assemble the prompt
    prompt_parts = [
        role_prompt,
        "",
        base_template.format(
            role_name=role_name,
            feature_name=feature_name,
            task_description=task_description,
            context_json=context_json,
        ),
        "",
        "## Expected Response Schema",
        "```json",
        schema_json,
        "```",
    ]

    return "\n".join(prompt_parts)

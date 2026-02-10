"""Response schemas for LLM-powered agents.

Defines Pydantic models for structured agent responses.
Each agent role has a specific schema extending the base.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DecisionCategory(str, Enum):
    """Categories for agent decisions"""
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UX = "user_experience"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class Decision(BaseModel):
    """A decision made by an agent"""
    text: str = Field(description="The decision made")
    rationale: str = Field(description="Why this decision was made")
    category: DecisionCategory = Field(description="Category of the decision")


class CodeSnippet(BaseModel):
    """A code snippet produced by an agent"""
    language: str = Field(description="Programming language")
    filename: Optional[str] = Field(default=None, description="Suggested filename")
    code: str = Field(description="The code content")
    description: Optional[str] = Field(default=None, description="What this code does")


class BaseAgentResponse(BaseModel):
    """Base response schema - all agents return these fields"""
    analysis: str = Field(description="Assessment of the task and current situation")
    approach: str = Field(description="How the agent will tackle this task")
    decisions: List[Decision] = Field(default_factory=list, description="Decisions made")
    concerns: List[str] = Field(default_factory=list, description="Potential issues or risks")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


# ============================================================================
# Role-Specific Response Schemas
# ============================================================================

class ArchitectResponse(BaseAgentResponse):
    """Response schema for Software Architect"""
    architecture_patterns: List[str] = Field(
        default_factory=list,
        description="Architecture patterns to use (MVC, microservices, etc.)"
    )
    component_diagram: str = Field(
        default="",
        description="ASCII or mermaid diagram of components"
    )
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Recommended technologies"
    )
    integration_points: List[str] = Field(
        default_factory=list,
        description="External systems and integration points"
    )


class BackendResponse(BaseAgentResponse):
    """Response schema for Backend Developer"""
    endpoints: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="API endpoints to create (method, path, description)"
    )
    data_models: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Database models or schemas"
    )
    code_snippets: List[CodeSnippet] = Field(
        default_factory=list,
        description="Implementation code"
    )
    performance_notes: List[str] = Field(
        default_factory=list,
        description="Performance considerations"
    )


class FrontendResponse(BaseAgentResponse):
    """Response schema for Frontend Developer"""
    components: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="React components to create"
    )
    state_management: str = Field(
        default="",
        description="State management approach"
    )
    code_snippets: List[CodeSnippet] = Field(
        default_factory=list,
        description="Implementation code"
    )
    accessibility_notes: List[str] = Field(
        default_factory=list,
        description="Accessibility considerations"
    )


class SecurityResponse(BaseAgentResponse):
    """Response schema for Security Specialist"""
    vulnerabilities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified security vulnerabilities"
    )
    risk_level: str = Field(
        default="medium",
        description="Overall risk level (low/medium/high/critical)"
    )
    mitigations: List[str] = Field(
        default_factory=list,
        description="Recommended security fixes"
    )
    compliance_notes: List[str] = Field(
        default_factory=list,
        description="Compliance considerations (GDPR, SOC2, etc.)"
    )


class DBAResponse(BaseAgentResponse):
    """Response schema for Database Administrator"""
    schema_changes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Table/column changes needed"
    )
    indexes: List[str] = Field(
        default_factory=list,
        description="Recommended indexes"
    )
    queries: List[CodeSnippet] = Field(
        default_factory=list,
        description="SQL queries"
    )
    migration_steps: List[str] = Field(
        default_factory=list,
        description="Migration procedure"
    )


class UIUXResponse(BaseAgentResponse):
    """Response schema for UI/UX Designer"""
    user_flows: List[str] = Field(
        default_factory=list,
        description="User journey steps"
    )
    wireframe_description: str = Field(
        default="",
        description="Layout and wireframe description"
    )
    design_tokens: Dict[str, Any] = Field(
        default_factory=dict,
        description="Colors, spacing, typography"
    )
    accessibility_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated accessibility score"
    )


class ITAdminResponse(BaseAgentResponse):
    """Response schema for IT Administrator"""
    infrastructure: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Required services and resources"
    )
    deployment_steps: List[str] = Field(
        default_factory=list,
        description="Deployment procedure"
    )
    monitoring_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Monitoring and alerting setup"
    )
    scaling_notes: List[str] = Field(
        default_factory=list,
        description="Scaling considerations"
    )


# ============================================================================
# Schema Registry
# ============================================================================

RESPONSE_SCHEMAS = {
    "software_architect": ArchitectResponse,
    "backend_developer": BackendResponse,
    "frontend_developer": FrontendResponse,
    "security_specialist": SecurityResponse,
    "database_administrator": DBAResponse,
    "ui_ux_designer": UIUXResponse,
    "it_administrator": ITAdminResponse,
}


def get_schema_for_role(role: str) -> type:
    """Get the response schema for a given role"""
    return RESPONSE_SCHEMAS.get(role, BaseAgentResponse)

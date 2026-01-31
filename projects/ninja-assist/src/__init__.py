"""Ninja Assist - Neurodivergent-friendly AI interface layer."""

from .intent_router import classify_intent, route_request, Intent, IntentCategory

__all__ = ["classify_intent", "route_request", "Intent", "IntentCategory"]

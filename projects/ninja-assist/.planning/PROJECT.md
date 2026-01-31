# Ninja Assist

## Vision
A neurodivergent-friendly AI interface layer that routes plain-language requests to the right tools automatically, minimizing cognitive load and eliminating the need to remember commands.

## Problem
- Too many tools/commands to remember
- Cognitive overhead causes friction and negative feelings
- Current workflow requires knowing which tool to use

## Solution
Hybrid A+C architecture:
- **Layer 1:** Lightweight pattern matching (zero tokens)
- **Layer 2:** Context state files (persistent, no re-analysis)  
- **Layer 3:** Auto-triggers on heartbeats (background)
- **Layer 4:** Full LLM only when needed (ambiguous requests)

## Core Use Cases
1. **Code** → Claude Code / GSD
2. **Research** → web_search / Shadow Council
3. **Install/Update** → exec / package managers
4. **Design/Brainstorm** → Shadow Council / structured prompts

## Design Principles
- AUTOMATION IS NON-NEGOTIABLE (user has ADHD + Autism)
- Token efficient - don't waste context
- Plain language in, right tool out
- Proactive, not reactive when possible
- Never make user feel stupid

## Target User
Neurodivergent Ninja 🥷 - ADHD + Autism

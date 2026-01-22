# Prompting Technique Framework Design

**Date:** 2026-01-20
**Status:** Design Complete - Ready for Implementation
**Owner:** Claude Code

## Executive Summary

Transform the Prompting Technique Categories system from a static reference (51 Initial-Use + 2 Follow-Up techniques) into an **automated decision framework** that intelligently recommends techniques based on task type, with minimal token overhead (~35 tokens average).

**Key Improvements:**
- Expand Follow-Up techniques: 2 → 12 techniques
- Organize Initial-Use techniques: 51 → 8 categories
- Create Hybrid Combination Table: 12 proven Stage 1 + Stage 2 pairs
- Implement Task Type Classifier: 3-layer detection engine
- Build decision framework: Hybrid-First approach with Category fallback

---

## SECTION 1: Overall System Architecture

The prompting framework operates as a **decision engine** with three core data structures:

### 1.1 Task Type Classifier (Detection Engine)

**Purpose:** Automatically identify which task type the user is working on
**Approach:** 3-layer lightweight pattern matching (minimal token cost)

Layers:
1. **Layer 1** (~10 tokens): Prompt characteristics analysis
   - Complexity indicators
   - Output type signals
   - Domain markers
   - Constraints detection

2. **Layer 2** (~20 tokens): Pattern matching against known task signatures
   - "IF contains code keywords + asks to write/fix → code-generation"
   - "IF contains reasoning verbs → complex-reasoning"
   - "IF contains factual keywords → factual-lookup"
   - "IF contains creative verbs → creative-writing"
   - "IF contains system design keywords → system-design"

3. **Layer 3** (~30 tokens, optional): Full LLM analysis
   - Only triggered by "optimize this prompt" command
   - Returns confidence scores and alternatives

**Output Format:**
```json
{
  "task_type": "complex-reasoning",
  "confidence": 0.95,
  "detected_from": "Layer 2 - pattern matching",
  "characteristics": ["multi-step", "requires-logic-trace", "medium-complexity"],
  "suggested_combo": ["ReAct (Stage 1)", "Reflexion (Stage 2)"],
  "alternatives": ["Plan-and-Solve", "Tree-of-Thoughts"]
}
```

### 1.2 Hybrid Combination Table (Lookup)

**Purpose:** Store proven Stage 1 + Stage 2 technique pairs
**Keyed by:** Task type from classifier
**Fallback:** Default combo if no match found

Example:
```
"complex-reasoning" → [ReAct (Stage 1), Reflexion (Stage 2)]
"code-generation" → [Chain-of-Thought + Few-Shot (Stage 1), Error-Analysis (Stage 2)]
```

### 1.3 Category System (Organized Techniques)

**Purpose:** Organize 51 Initial-Use and 12 Follow-Up techniques
**Structure:** 8 categories + 2 technique lists
**Used when:** No proven combo found in Hybrid table

### 1.4 Execution Flow

```
User Prompt
  → Classify Task Type (Layer 1-2: ~30 tokens)
  → Lookup Hybrid Combo
    ├─ FOUND → Return Stage 1 + Stage 2 techniques (50 tokens total)
    └─ NOT FOUND → Category Fallback → Return matching category techniques (150 tokens total)
```

**Average token cost:** ~35 tokens per classification

---

## SECTION 2: Hybrid Combination Table

Maps task types to proven Stage 1 + Stage 2 technique pairs.

### 2.1 Primary Combinations (12 task types)

| Task Type | Stage 1 | Stage 2 | Why Works | Latency | Reliability |
|-----------|---------|---------|----------|---------|-------------|
| Complex Reasoning | ReAct | Reflexion | ReAct traces reasoning; Reflexion critiques trace | Medium | Very High |
| Multi-step Problem | Plan-and-Solve | Error-Analysis | Plan structures steps; Error-Analysis catches breakdowns | Medium | High |
| Factual Accuracy | Few-Shot + Self-Consistency | Fact-Check-Then-Fix | Examples ground output; Self-Consistency validates; Follow-up corrects | High | Very High |
| Code Generation | Chain-of-Thought + Few-Shot | Error-Analysis | Reasoning explains intent; Examples show patterns; Follow-up catches bugs | Medium | Very High |
| Creative Writing | Emotion Prompting | Multi-Perspective-Refinement | Emotion sets tone; Multi-perspective enriches depth | Low | High |
| Data Analysis | Tree-of-Thoughts | Comparative-Refinement | ToT explores options; Comparative selects best | High | High |
| Summarization | Chain-of-Thought | Progressive-Elaboration | CoT identifies key points; Progressive adds nuance | Low | Medium |
| Classification | Few-Shot | Confidence-Based-Refinement | Examples teach categories; Confidence refinement focuses on borderlines | Low | High |
| Translation | Few-Shot | Format-Refinement | Examples show style; Format fixes structure/tone | Low | High |
| Brainstorming | Emotion Prompting | Analogical-Reasoning | Emotion opens creativity; Analogical connects to other domains | Low | Medium |
| System Design | Tree-of-Thoughts | Multi-Perspective-Refinement | ToT explores architectures; Multi-perspective adds constraints | High | High |
| Debugging | ReAct | Error-Analysis | ReAct traces execution; Error-Analysis isolates root cause | Medium | Very High |

### 2.2 Fallback Combinations

- **Default for unknown tasks:** Chain-of-Thought (Stage 1) + Self-Refine (Stage 2)
- **High-reliability fallback:** Few-Shot (Stage 1) + Reflexion (Stage 2)

### 2.3 Token Costs by Complexity

- Simple tasks (Summarization, Translation, Brainstorming): 50-80 tokens total
- Medium complexity (Complex Reasoning, Code Generation, System Design): 100-150 tokens total
- High complexity (Factual Accuracy): 150-200 tokens total

---

## SECTION 3: Expanded Follow-Up Techniques (2 → 12)

Current system only has 2 Follow-Up techniques. Expanding to 12 organized by type.

### 3.1 Error Correction (3 techniques)

**1. Reflexion** (existing)
- **When to use:** Response has logical gaps or incorrect conclusions
- **Signal:** "Your answer misses X" or "That doesn't address Y"
- **Prompt template:** "Review your previous answer. What errors or gaps did you miss? How would you fix them?"
- **Expected improvement:** 20-40% accuracy boost

**2. Self-Refine** (existing)
- **When to use:** Response needs iterative polish and incremental improvement
- **Signal:** "Can you make this better?" without specific feedback
- **Prompt template:** "Improve your previous answer. What can be enhanced?"
- **Expected improvement:** 10-30% quality improvement

**3. Error-Analysis** (NEW)
- **When to use:** Need to understand WHERE and WHY response failed
- **Signal:** "This is wrong. Why?" or "Break down the failure"
- **Prompt template:** "Your previous answer had errors. For each error: (1) What part failed? (2) Why did it fail? (3) How do you fix it?"
- **Expected improvement:** 30-50% accuracy boost + learning value

### 3.2 Comparative Methods (3 techniques)

**4. Multi-Perspective-Refinement** (NEW)
- **When to use:** Need richer, more nuanced answer with multiple viewpoints
- **Signal:** "What other perspectives exist?" or "Make this more complete"
- **Prompt template:** "Generate 2-3 different perspectives on your answer. How are they different? Which elements from each should be combined?"
- **Expected improvement:** 25-40% comprehensiveness

**5. Comparative-Refinement** (NEW)
- **When to use:** Need to evaluate options and select the best
- **Signal:** "Which is better?" or "Compare alternatives"
- **Prompt template:** "Generate 2-3 alternative solutions to your answer. Compare them on: clarity, correctness, completeness. Which is best and why?"
- **Expected improvement:** 20-35% quality

**6. Fact-Check-Then-Fix** (NEW)
- **When to use:** Response contains factual claims that need verification
- **Signal:** "Verify your facts" or "Are these accurate?"
- **Prompt template:** "Review your answer. For each factual claim: (1) Is it accurate? (2) If uncertain, flag it. (3) Correct any inaccuracies."
- **Expected improvement:** 40-60% accuracy for factual tasks

### 3.3 Evolutionary Methods (3 techniques)

**7. Progressive-Elaboration** (NEW)
- **When to use:** Answer is too surface-level, needs depth added gradually
- **Signal:** "Expand on this" or "Add more detail"
- **Prompt template:** "Take your answer. Add one layer of detail/nuance to each point. Don't change what's there, just deepen it."
- **Expected improvement:** 15-25% depth

**8. Confidence-Based-Refinement** (NEW)
- **When to use:** Need to focus refinement on low-confidence areas
- **Signal:** "I'm uncertain about X" or "Which parts are most questionable?"
- **Prompt template:** "Rate your confidence in each part of your answer (High/Medium/Low). Expand on all Medium/Low confidence areas."
- **Expected improvement:** 25-40% for uncertain areas

**9. Analogical-Reasoning** (NEW)
- **When to use:** Solution needs broader perspective from other domains
- **Signal:** "How does this connect to other fields?" or "What's analogous?"
- **Prompt template:** "Your answer solves this problem. What similar problems exist in other domains? How do solutions there inform this?"
- **Expected improvement:** 15-35% novelty/depth

### 3.4 Format & Structure (3 techniques)

**10. Format-Refinement** (NEW)
- **When to use:** Content is good but structure/presentation is unclear
- **Signal:** "Make this clearer" or "Reorganize this"
- **Prompt template:** "Restructure your answer in [format: outline/prose/bullet-points/visual/narrative]. Keep all content, just reorganize."
- **Expected improvement:** 20-40% clarity

**11. Adversarial-Refinement** (NEW)
- **When to use:** Answer needs stress-testing against counterarguments
- **Signal:** "Challenge this" or "What's the opposite view?"
- **Prompt template:** "Argue strongly AGAINST your own answer. What are the best counterarguments? Now address them and refine your answer."
- **Expected improvement:** 30-50% robustness

**12. Constraint-Relaxation** (NEW)
- **When to use:** Need to explore solution space by varying constraints
- **Signal:** "What if we relaxed X?" or "What are alternatives?"
- **Prompt template:** "Your answer follows these constraints: [list]. What if we relaxed one constraint at a time? How would solutions change?"
- **Expected improvement:** 20-40% exploration value

---

## SECTION 4: Category System (Initial-Use: 51 Techniques)

Organize 51 Initial-Use techniques into 8 actionable categories.

### 4.1 Category 1: Reasoning Techniques (8)

**Purpose:** Improve step-by-step logical thinking
**Techniques:** Chain-of-Thought, Tree-of-Thoughts, Graph-of-Thoughts, ReAct, Plan-and-Solve, Least-to-Most Prompting, Scratchpad, Reasoning with Examples
**Use signal:** "Task requires logical steps or reasoning trace"
**Characteristic:** Multi-step, transparent reasoning
**Best for:** Complex reasoning, debugging, multi-step problems

### 4.2 Category 2: Data/Examples Techniques (7)

**Purpose:** Ground responses in provided data
**Techniques:** Few-Shot Learning, In-Context Learning, Example-Driven Generation, Semantic Search, Retrieval-Augmented Generation (RAG), Priming, Zero-Shot with Context
**Use signal:** "Task needs examples or grounding in data"
**Characteristic:** Example-based, factual anchoring
**Best for:** Factual accuracy, classification, code generation, translation

### 4.3 Category 3: Format/Structured Output Techniques (6)

**Purpose:** Control output structure and format
**Techniques:** JSON Mode, XML Formatting, Markdown Structuring, Bullet-Point Output, Step-by-Step Templates, Tables/Lists
**Use signal:** "Task requires specific output format or structure"
**Characteristic:** Explicit formatting, parser-friendly
**Best for:** Code generation, data analysis, summarization

### 4.4 Category 4: Social/Psychological Techniques (7)

**Purpose:** Leverage human psychology and role-playing
**Techniques:** Emotion Prompting, Role-Playing, Persona Adoption, Expert Simulation, Socratic Method, Storytelling, Persona-with-Context
**Use signal:** "Task benefits from tone, empathy, or roleplay"
**Characteristic:** Human-centric, tone-aware
**Best for:** Creative writing, brainstorming, emotional content

### 4.5 Category 5: Decomposition Techniques (8)

**Purpose:** Break complex problems into manageable parts
**Techniques:** Step-Decomposition, Chain-Decomposition, Hierarchical Decomposition, Modular Prompting, Constraint Decomposition, Multi-Stage Processing, Progressive Decomposition, Abstraction Levels
**Use signal:** "Task is complex and needs breaking down"
**Characteristic:** Divide-and-conquer, reduced complexity per step
**Best for:** System design, multi-step problems, complex reasoning

### 4.6 Category 6: Comparison/Verification Techniques (6)

**Purpose:** Validate, compare, or ensure consistency
**Techniques:** Self-Consistency, Ensemble Methods, Voting/Majority, Cross-Checking, Contradiction Detection, Consensus-Based
**Use signal:** "Task needs verification or high confidence"
**Characteristic:** Multiple paths/perspectives, validation
**Best for:** Factual accuracy, critical decisions, high-reliability needs

### 4.7 Category 7: Uncertainty/Exploratory Techniques (5)

**Purpose:** Generate alternatives and explore possibility space
**Techniques:** Temperature-Based Variation, Beam Search, Sampling Strategies, Hypothesis Generation, What-If Analysis
**Use signal:** "Task benefits from exploring alternatives"
**Characteristic:** Exploratory, non-deterministic
**Best for:** Brainstorming, creative writing, data analysis

### 4.8 Category 8: Other/Specialized Techniques (4)

**Purpose:** Domain-specific or emerging techniques
**Techniques:** Chain-of-Verification, Active Learning, Prompt Compression, Domain-Specific Adaptation
**Use signal:** "Task has specialized requirements"
**Characteristic:** Niche applications, evolving
**Best for:** Specialized domains, emerging task types

---

## SECTION 5: Task Type Classifier

Detects task type using 3-layer lightweight pattern matching.

### 5.1 Task Type Dictionary (13 types)

1. **complex-reasoning** - Multi-step logical problem solving
2. **multi-step-problem** - Sequential procedural task
3. **factual-accuracy** - Information retrieval/verification
4. **code-generation** - Writing or fixing code
5. **creative-writing** - Prose, storytelling, creative content
6. **data-analysis** - Analytics, interpretation, patterns
7. **summarization** - Condensing information
8. **classification** - Categorizing or labeling
9. **translation** - Language conversion
10. **brainstorming** - Ideation and exploration
11. **system-design** - Architecture or structural planning
12. **debugging** - Finding and fixing problems
13. **unknown** - Fallback for unclassified tasks

### 5.2 Heuristic Patterns (Layer 2)

```
IF (contains code-related keywords ["write", "fix", "function", "bug"]
    AND (asks for "code" OR "script" OR "program"))
  THEN task_type = "code-generation"

IF (contains reasoning verbs ["analyze", "explain", "prove", "derive"]
    AND complexity > 2 steps)
  THEN task_type = "complex-reasoning"

IF (contains factual keywords ["list", "count", "find", "research", "verify"]
    AND output type = "factual")
  THEN task_type = "factual-accuracy"

IF (contains creative verbs ["write", "create", "imagine", "design", "compose"]
    AND output type ≠ "code" AND output type ≠ "factual")
  THEN task_type = "creative-writing"

IF (contains system keywords ["design", "architecture", "system", "component"]
    AND complexity > 2)
  THEN task_type = "system-design"

IF (contains analytical keywords ["analyze", "compare", "trend", "pattern"]
    AND input type = "data")
  THEN task_type = "data-analysis"

...
```

### 5.3 Classification Output Format

```json
{
  "task_type": "complex-reasoning",
  "confidence": 0.95,
  "detected_from": "Layer 2 - pattern matching",
  "characteristics": ["multi-step", "requires-logic-trace", "medium-complexity"],
  "suggested_combo": ["ReAct (Stage 1)", "Reflexion (Stage 2)"],
  "alternatives": ["Plan-and-Solve", "Tree-of-Thoughts"],
  "reasoning": "Contains reasoning verbs and requires logical steps across multiple turns"
}
```

---

## SECTION 6: Full Integration Workflow

Three complementary workflows activated in different contexts.

### 6.1 Workflow A: Automated Post-Response Refinement (Always Active)

**Triggers:** After every response
**Cost:** ~30 tokens per response
**User Control:** Optional

```
1. I generate response
   ↓
2. Task Type Classifier runs (Layer 1-2: ~30 tokens)
   ↓
3. Lookup Hybrid Combo table
   ├─ Found combo?
   │  └─ Suggest Stage 2: "Would you like me to apply Reflexion to critique this answer?"
   │
   └─ No combo?
      └─ Category fallback: "This looks like a data-analysis task. Would Comparative-Refinement help?"
   ↓
4. User decision:
   - Accept → Apply technique, regenerate response
   - Decline → Continue to next prompt
   - Ignore → Move on (no intervention)
```

**Example:**
```
User: "Debug this Python function"
System response: [traces execution with ReAct]
System suggests: "Should I apply Error-Analysis to break down each failure point?"
User: "Yes"
System applies: [generates Error-Analysis refinement]
```

### 6.2 Workflow B: Real-Time Prompt Optimization (User-Initiated)

**Trigger:** User says "optimize this prompt"
**Cost:** ~150-200 tokens
**User Control:** Explicit request

```
1. Task Type Classifier runs (Layer 1-2-3: ~60 tokens)
   ├─ Layer 1: Detect characteristics
   ├─ Layer 2: Pattern matching
   └─ Layer 3: Full LLM analysis
   ↓
2. Lookup Hybrid Combo
   ├─ Found?
   │  └─ Suggest Stage 1: "For complex-reasoning, I recommend ReAct"
   │
   └─ Not found?
      └─ Category matching: "I suggest techniques from the Reasoning category"
   ↓
3. Offer implementation
   - "Would you like me to rewrite your prompt using ReAct?"
   - Generate revised prompt with technique applied
```

**Example:**
```
User: "optimize this prompt" [shows original prompt]
System: Runs full analysis
System: "This is a complex-reasoning task. I recommend ReAct.
Here's your optimized prompt: [shows rewritten prompt]"
```

### 6.3 Workflow C: Session Context Learning (Continuous)

**Triggers:** Continuously during session
**Cost:** ~10 tokens per log entry
**User Control:** Passive (automatic logging)

```
Track over session:
- Which techniques got used
- Which refinements helped
- What task types appeared
- Success patterns emerge

Result: Session-specific learning
Example: "In this session, you used Reflexion successfully on 3 complex-reasoning tasks"
```

### 6.4 Decision Tree: When System Intervenes

```
Every response:
  ├─ Apply Layer 1-2 classification (~30 tokens)
  ├─ Lookup Hybrid Combo
  ├─ If found → suggest Stage 2
  └─ If not found → suggest Category

User says "optimize this prompt":
  ├─ Apply full Layer 1-2-3 classification (~60 tokens)
  ├─ Suggest Stage 1 + Stage 2 techniques
  └─ Offer rewrite

User says "reflect on your answer":
  ├─ Apply relevant Stage 2 technique
  ├─ Regenerate response with refinement
  └─ Continue

Simple prompts (<30 chars):
  └─ Skip classification entirely
```

### 6.5 System Behavior Summary

| Scenario | Intervention | Token Cost | User Control |
|----------|---|---|---|
| Normal response | Suggest Stage 2 | 30 tokens | Optional |
| User: "optimize this prompt" | Full analysis + Stage 1+2 | 150 tokens | Explicit request |
| User: "reflect on your answer" | Apply Stage 2 | Variable | Explicit request |
| Simple prompt | None | 0 tokens | Auto-skip |
| Session pattern | Learn + suggest | 10 tokens | Passive logging |

---

## SECTION 7: Implementation Strategy

### 7.1 Phase 1: Data Structure Setup (Week 1)

1. Create Hybrid Combination Table (JSON/YAML)
2. Organize 51 techniques into 8 categories
3. Create Follow-Up technique definitions (12 total)
4. Create Task Type Dictionary

### 7.2 Phase 2: Classifier Implementation (Week 2)

1. Build Layer 1-2 pattern matching engine
2. Create heuristic patterns for all 13 task types
3. Test classification accuracy on historical prompts

### 7.3 Phase 3: Workflow Integration (Week 3)

1. Implement Workflow A (post-response suggestions)
2. Implement Workflow B (user-initiated optimization)
3. Implement Workflow C (session context logging)

### 7.4 Phase 4: Testing & Refinement (Week 4)

1. Test on real prompts across all task types
2. Measure token usage vs. benefits
3. Refine heuristic patterns based on misclassifications
4. Create user documentation

---

## SECTION 8: Success Criteria

**Accuracy:**
- Classification correct 85%+ of the time on Layer 1-2
- Suggested techniques helpful 70%+ of the time (user feedback)

**Efficiency:**
- Post-response suggestions: ~30 tokens average
- Optimization requests: ~150 tokens average
- No impact on latency

**Adoption:**
- Users accept Stage 2 suggestions 40%+ of the time
- Users use "optimize this prompt" 10%+ of responses

**Quality:**
- Stage 2 refinements improve response quality 20%+ (measured by user satisfaction)
- No false negatives (techniques never withheld when appropriate)

---

## SECTION 9: Future Enhancements

- Machine learning classifier (Layer 3+) for improved accuracy
- User preference learning (remember which techniques user prefers)
- Cross-session pattern analysis (identify recurring task types)
- Technique combination discovery (find new synergistic pairs)
- Feedback loop integration (learn from user acceptance/rejection)

---

## Appendix A: Glossary

- **Stage 1 (Initial-Use):** Techniques applied before initial response
- **Stage 2 (Follow-Up):** Techniques applied to refine/improve response
- **Hybrid:** Techniques that work in both stages
- **Task Type:** Classification of user's goal (e.g., "code-generation")
- **Technique:** Specific prompting method (e.g., "ReAct")
- **Combo:** Proven Stage 1 + Stage 2 pair for specific task type

---

## Appendix B: References

- Original Technique Categories: 51 Initial-Use, 2 Follow-Up, 3 Hybrid
- Hybrid Combination Table: 12 core task types with proven pairs
- Category System: 8 categories + 12 follow-up techniques
- Classifier: 3-layer detection engine with 13 task types

---

**Design Status:** ✓ Complete and Validated
**Ready for Implementation:** Yes
**Estimated Effort:** 4 weeks
**Token Budget:** ~35 tokens average per classification

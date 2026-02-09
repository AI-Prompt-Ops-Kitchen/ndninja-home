# Shadow Council Integration Guide

## Overview

The Shadow Council integration adds multi-LLM code review to the CLI Agent Benchmark Arena, providing deeper quality assessment beyond static analysis (pylint/flake8).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Agent Executes Task → Generate Code → Test Suite           │
│                                           │                   │
│                                           ├─ Pytest          │
│                                           ├─ Pylint/Flake8   │
│                                           └─ Shadow Council  │
│                                                   │           │
│                                           ┌───────▼────────┐ │
│                                           │ 4 LLM Judges   │ │
│                                           ├────────────────┤ │
│                                           │ Claude 4.5     │ │
│                                           │ GPT-4 Turbo    │ │
│                                           │ Gemini 2.0     │ │
│                                           │ Perplexity     │ │
│                                           └───────┬────────┘ │
│                                                   │           │
│                                           Consensus Score     │
│                                           (0-100)            │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Dimensional Grading
- **Functional Accuracy** (30%): Correctness and task completion
- **Error Handling** (25%): Exception handling and edge cases
- **Best Practices** (25%): Language conventions and patterns
- **Readability** (20%): Code clarity and documentation

### Council Members
1. **Claude Sonnet 4.5** - Chief Architect & Code Quality
2. **GPT-4 Turbo** - Security Auditor & Best Practices
3. **Gemini 2.0 Flash** - Innovation & Code Excellence
4. **Perplexity Sonar Pro** - Industry Standards & Patterns

### Consensus System
- High Consensus: Score variance < 8 points
- Medium Consensus: Score variance 8-15 points
- Low Consensus: Score variance > 15 points (5% penalty)

## Integration Options

### Option 1: Enhanced Quality Score (Recommended)

Replace or augment the existing pylint/flake8 quality score:

```python
# In adapters/kimi.py, adapters/claude.py, etc.
from quality.shadow_council_integration import ShadowCouncilGrader

# After code generation
generated_code = self._read_generated_files(task_dir)

# Get Shadow Council review
grader = ShadowCouncilGrader()
llm_score, review = grader.grade_code(
    generated_code,
    task.description,
    language="python"
)

# Use as quality score (0-100)
benchmark_result = BenchmarkResult(
    # ... other fields ...
    quality_score=llm_score  # Replace static analysis score
)
```

### Option 2: Hybrid Approach

Combine static analysis with LLM review:

```python
from quality.analyzer import QualityAnalyzer
from quality.shadow_council_integration import ShadowCouncilGrader

# Static analysis (fast, deterministic)
analyzer = QualityAnalyzer()
static_score = analyzer.analyze(generated_files)

# LLM review (deep, contextual)
grader = ShadowCouncilGrader()
llm_score, review = grader.grade_code(code, task.description)

# Weighted combination (70% static, 30% LLM)
final_quality_score = (static_score * 0.7) + (llm_score * 0.3)

benchmark_result = BenchmarkResult(
    quality_score=final_quality_score
)
```

### Option 3: New Scoring Dimension

Add as 6th dimension alongside existing 5:

```python
# In scoring.py

@dataclass
class Score:
    speed_score: float          # 25% weight
    correctness_score: float    # 40% weight
    cost_score: float           # 15% weight
    autonomy_score: float       # 12% weight
    quality_score: float        # 5% weight (reduced from 8%)
    llm_review_score: float     # 3% weight (NEW)
    total_score: float

# Update ScoringEngine.calculate_score() to include LLM review
```

## Usage Examples

### Basic Usage

```python
from quality.shadow_council_integration import ShadowCouncilGrader

grader = ShadowCouncilGrader()

code = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""

score, review = grader.grade_code(
    code,
    task_description="Implement quicksort algorithm",
    language="python"
)

print(f"Score: {score}/100")
print(grader.generate_report(review))
```

### Integration with Benchmark Runner

```python
# In run_cli_benchmarks.py

from quality.shadow_council_integration import ShadowCouncilGrader

def run_benchmark_with_council(agent_name, task):
    # ... existing benchmark code ...

    # After code generation and testing
    grader = ShadowCouncilGrader()

    generated_code = read_files(task_dir / "*.py")
    llm_score, review = grader.grade_code(
        generated_code,
        task.description
    )

    # Store detailed review in database
    db.save_llm_review(
        result_id=result_id,
        score=llm_score,
        review=review
    )

    # Update quality score
    benchmark_result.quality_score = llm_score

    return benchmark_result
```

## Cost Considerations

### Simulated Mode (Default)
- **Cost**: $0
- **Speed**: Instant
- **Use for**: Development, testing, CI/CD

### Real LLM Mode
- **Cost**: ~$0.05-0.10 per review (4 LLM calls)
- **Speed**: 30-60 seconds
- **Use for**: Final benchmarks, production comparisons

```python
# Enable real LLM calls
grader = ShadowCouncilGrader(use_real_llms=True)
```

## Database Schema Enhancement

Add LLM review tracking:

```sql
-- Add to cli_agent_benchmark_results table
ALTER TABLE cli_agent_benchmark_results
ADD COLUMN llm_review_score NUMERIC(5,2),
ADD COLUMN llm_consensus_level VARCHAR(20),
ADD COLUMN llm_review_details JSONB;

-- Example data
{
  "final_score": 86.2,
  "consensus_level": "High",
  "judges": [...],
  "dimensions": {
    "functional_accuracy": 88.8,
    "error_handling": 84.5,
    "best_practices": 85.0,
    "readability": 86.8
  },
  "top_strengths": [...],
  "top_improvements": [...]
}
```

## Dashboard Integration

Update HTML dashboard to show Shadow Council results:

```html
<!-- In reporting/templates/dashboard.html -->

<div class="llm-review">
    <h3>🌙 Shadow Council Review</h3>
    <div class="council-score">
        Score: {{ result.llm_review_score }}/100
        <span class="consensus-{{ result.llm_consensus }}">
            {{ result.llm_consensus }} Consensus
        </span>
    </div>

    <div class="judge-scores">
        {% for judge in result.llm_review_details.judges %}
        <div class="judge">
            <strong>{{ judge.name }}</strong>: {{ judge.score }}/100
        </div>
        {% endfor %}
    </div>

    <div class="dimensions">
        {% for dim, score in result.llm_review_details.dimensions.items() %}
        <div class="dimension-bar">
            <span>{{ dim|replace('_', ' ')|title }}</span>
            <div class="progress" style="width: {{ score }}%"></div>
        </div>
        {% endfor %}
    </div>
</div>
```

## Performance Optimization

### Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def grade_with_council_async(code, task):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        score, review = await loop.run_in_executor(
            executor,
            grader.grade_code,
            code,
            task.description
        )
    return score, review
```

### Caching
```python
import hashlib
import json

def grade_with_cache(code, task):
    # Generate cache key
    cache_key = hashlib.sha256(
        f"{code}{task.description}".encode()
    ).hexdigest()

    cache_file = Path(f".cache/council/{cache_key}.json")

    # Check cache
    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
            return cached['score'], cached['review']

    # Grade and cache
    score, review = grader.grade_code(code, task.description)

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump({'score': score, 'review': review}, f)

    return score, review
```

## Testing

```bash
# Run Shadow Council integration demo
cd benchmarks/cli_agent_arena
python3 quality/shadow_council_integration.py

# Run with custom code
python3 -c "
from quality.shadow_council_integration import ShadowCouncilGrader
grader = ShadowCouncilGrader()
code = open('my_code.py').read()
score, review = grader.grade_code(code, 'My task')
print(grader.generate_report(review))
"
```

## Roadmap

### Phase 1 (Current)
- ✅ Shadow Council integration framework
- ✅ Simulated multi-LLM reviews
- ✅ 4-dimensional grading system
- ✅ Consensus scoring

### Phase 2 (Next)
- ⬜ Real LLM API integration
  - Anthropic API for Claude
  - Google AI for Gemini
  - OpenAI for GPT-4
  - Perplexity API
- ⬜ Cost tracking and budgets
- ⬜ Review caching system

### Phase 3 (Future)
- ⬜ Configurable judge panel
- ⬜ Custom grading rubrics
- ⬜ Historical trend analysis
- ⬜ A/B testing of judge combinations
- ⬜ Fine-tuned domain-specific judges

## Example Output

```
======================================================================
🌙 SHADOW COUNCIL CODE REVIEW
======================================================================

**Final Score**: 86.2/100 (⭐⭐⭐⭐ 4.2/5.0)
**Consensus**: High
**Score Range**: 82-90
**Methodology**: Shadow Council Multi-LLM Consensus

## Council Members
- **Claude Sonnet 4.5** (Chief Architect & Code Quality): 90/100 ⭐⭐⭐⭐
- **GPT-4 Turbo** (Security Auditor & Best Practices): 85/100 ⭐⭐⭐⭐
- **Gemini 2.0 Flash** (Innovation & Code Excellence): 88/100 ⭐⭐⭐⭐
- **Perplexity Sonar Pro** (Industry Standards & Patterns): 82/100 ⭐⭐⭐⭐

## Dimension Scores
- Functional Accuracy......  88.8/100 █████████████████░░░
- Error Handling...........  84.5/100 ████████████████░░░░
- Best Practices...........  85.0/100 █████████████████░░░
- Readability..............  86.8/100 █████████████████░░░

## ✅ Key Strengths
1. Excellent function decomposition
2. Efficient algorithm selection
3. Production-ready code structure
4. Input validation present
5. Good separation of concerns

## 🔧 Recommended Improvements
1. Add type hints for better IDE support
2. Include docstrings for public functions
3. Consider edge cases for empty inputs
4. Add unit tests alongside code
5. Add logging for debugging

======================================================================
Shadow Council Session Complete
======================================================================
```

## Benefits

### For Benchmark Accuracy
- **Deeper insights** beyond static analysis
- **Context-aware** evaluation (understands task intent)
- **Human-like** code review at scale
- **Multiple perspectives** from different models

### For Agent Development
- **Actionable feedback** for improving agents
- **Dimension breakdown** shows specific weaknesses
- **Best practices** suggestions from industry experts
- **Consensus validation** reduces single-model bias

### For Research
- **Compare LLM grading** vs human evaluation
- **Study inter-model agreement** on code quality
- **Identify systematic biases** in different judges
- **Benchmark the benchmarkers** (meta-evaluation)

## Conclusion

The Shadow Council integration elevates the CLI Agent Benchmark Arena from pure execution metrics to comprehensive code quality assessment. By combining multiple LLM perspectives with consensus-based scoring, we achieve more nuanced and reliable evaluation of AI coding agents.

**Recommended**: Start with **Option 2 (Hybrid Approach)** to balance cost, speed, and quality. Use simulated mode for development and real LLMs for final benchmarks.

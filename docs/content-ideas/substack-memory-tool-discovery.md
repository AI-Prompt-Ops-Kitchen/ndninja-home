# Substack Article: I Built an AI That Remembers My Tools (So I Don't Have To)

## Article Metadata
- **Platform**: Substack
- **Format**: Long-form technical narrative (8-12 min read)
- **Tone**: Personal, technical but accessible, story-driven
- **Target Audience**: Developers, AI enthusiasts, productivity hackers

---

## Title Options
1. **I Built an AI That Remembers My Tools (So I Don't Have To)** ⭐ RECOMMENDED
2. The Day I Forgot My Own LLM Council—And What I Built Because of It
3. Memory-Assisted Tool Discovery: How I Taught My AI to Remember What I Build
4. Building AI Memory: A Developer's Journey from Frustration to Solution

## Subtitle
"How conversation-driven tool discovery solved my 'I built this and forgot it exists' problem—and why nobody else has built this yet"

---

## Article Structure

### Opening Hook (150 words)
You ever build something really cool and then completely forget it exists?

Last week, I needed to compare VPN providers. I sat there wondering which LLMs to query, how to cross-reference their responses, how to avoid bias from any single model. I was about to manually query ChatGPT, Claude, Gemini, and Perplexity separately.

Then it hit me: **I already built this**.

Six months ago, I created "LLM Council"—a Python script that queries all four models in parallel and synthesizes their responses. It was sitting right there in my ~/projects folder. I'd used it 15 times before. And I completely forgot it existed.

This wasn't the first time. I've built dozens of custom tools—scripts, utilities, automations—that disappear into the void of my filesystem the moment I finish them.

So I built something to fix that. And it turns out, nobody else has built this either.

### The Problem (300 words)

**The Cognitive Load Problem**

As developers, we accumulate tools. Every frustration becomes a script. Every repeated task becomes automation. Over time, you build an arsenal of custom utilities that could save you hours—if only you could remember they exist.

The problem isn't documentation. I document everything. The problem is **contextual recall under cognitive load**.

When you're deep in a problem, your brain doesn't naturally think "Did I build a tool for this six months ago?" It thinks "How do I solve this NOW?"

**Why Existing Solutions Don't Work**

I tried:
- **README files**: Never look at them when I need them
- **Alfred/Raycast**: Great for launching, useless for discovering
- **Shell aliases**: Only work if I remember they exist
- **Documentation sites**: Another thing I need to remember to check

The fundamental issue: All these solutions require **me to remember to look**.

What I needed was a system that:
1. Understands what I'm working on (conversation context)
2. Knows what tools I have (tool registry)
3. Proactively suggests relevant tools (not just when I ask)
4. Runs automatically (no extra mental overhead)

And critically: It needed to work with **custom bash/Python tools**, not just fancy MCP servers.

### What Already Exists (400 words)

**MCP Tool Search (Anthropic, January 2026)**

Anthropic just rolled out MCP Tool Search—dynamic tool discovery for Claude Code. Instead of loading every tool definition upfront (massive token overhead), Claude discovers tools on-demand. 85% token reduction, huge accuracy improvements.

But here's the thing: **MCP Tool Search only works for MCP servers**.

If your tool is a Python script, a bash utility, or a custom automation? Not supported. You need to wrap it in an MCP server first.

**Existing Memory Systems**

There are several memory systems for AI assistants:
- **claude-mem**: Captures session context, compresses it with Claude's agent-sdk, injects it back
- **mcp-memory-keeper**: Persistent context management across sessions
- **task-orchestrator**: Task tracking and workflow automation
- **mem0**: Universal memory layer for AI agents

All excellent. But none of them do **tool discovery**.

They remember what you talked about. They don't suggest what tools you should use.

**Vector Databases for AI Memory**

Most AI memory systems use vector databases (Qdrant, Pinecone, Weaviate) for semantic similarity search.

Great for finding conceptually similar past conversations. Not great for "You mentioned distributed computing, so here's your Kage Bunshin cluster orchestrator."

That requires:
1. Keyword matching (not semantic similarity)
2. Tool metadata (location, command, usage patterns)
3. Performance optimization (can't wait 5 seconds for suggestions)
4. Integration with conversation flow (not a separate search step)

**The Gap**

Nobody had built:
- Memory + Tool Discovery + Hook-based Architecture
- Conversation-driven suggestions (not manual search)
- Custom tool support (bash/Python, not just MCP)
- Dual-mode: Proactive (session start) + Reactive (keyword detection)
- Zero external dependencies (no vector DB, no agent-sdk)

So I built it.

### The Solution: Memory-Assisted Tool Discovery (600 words)

**Architecture: Three Components**

**1. SessionStart Discovery**
When you start a Claude Code session, a bash hook runs automatically:
- Queries last 3 conversation summaries from PostgreSQL
- Extracts topics discussed (e.g., "distributed AI", "video production")
- Matches topics against tool keywords in the registry
- Scores and ranks tools by relevance
- Shows top 5 suggestions

Performance: **106ms** (barely noticeable)

**Example output:**
```
Suggested tools based on recent conversations:

1. Kage Bunshin (score: 38)
   Distributed AI orchestration across 4-node cluster
   Usage: cd ~/projects/kage-bunshin && python3 api/main.py

2. Video Production Pipeline (score: 30)
   Complete video workflow: voiceover, recording, assembly
   Usage: python3 production_orchestrator.py create <draft_id>
```

**2. Real-Time Keyword Detection**
When you submit a prompt, another hook scans for high-value keywords:
- Regex patterns for each tool (e.g., `multi-model|consensus|vpn analysis` → LLM Council)
- Rate limiting (1 suggestion per 5 messages—no spam)
- Duplicate prevention (won't suggest same tool twice)
- State persistence across hook invocations

Performance: **<50ms** (timeout enforced)

**Example:**
You type: "I need multi-model analysis for comparing frameworks"
Instantly: "💡 Detected tool suggestion: LLM Council - Multi-model analysis across 4 LLMs"

**3. Tool Registry (PostgreSQL)**
All tools stored in the `claude_memory` database:
- Table: `reference_info`, category: `tool`
- JSONB column for flexible metadata
- Standard PostgreSQL (no extensions, no vector DB)

Each tool has:
- Name, location, command
- Description, keywords, usage examples
- Performance stats, last used, use count

**Why PostgreSQL, Not a Vector DB?**

I get asked this a lot. Here's why:

**Vector DBs are for semantic similarity:**
- "distributed computing" ≈ "parallel processing" ≈ "cluster management"
- Great for fuzzy matching, finding conceptually similar things

**I needed exact keyword matching:**
- User says "multi-model" → Suggest LLM Council
- User says "72b" → Suggest Kage Bunshin cluster
- User says "docker environment" → Suggest Docker debugger

Keyword matching is:
- Faster (<10ms vs 100ms+)
- More predictable (no hallucinated similarity)
- Easier to debug (regex patterns, not embeddings)
- Simpler infrastructure (PostgreSQL already running)

Plus: 10 tools don't need vector search. If I had 10,000 tools? Different story.

**Implementation: Subagent-Driven Development**

Built the entire system in one focused session using subagent-driven development:

1. **Design Phase**: Brainstorming skill to explore architecture options
2. **Implementation**: 11 tasks, each handled by a fresh subagent
3. **Testing**: TDD throughout—20 tests, all passing
4. **Review**: Two-stage code review (spec compliance → code quality)
5. **Deployment**: Production-ready, all hooks installed

Each task got:
- Spec compliance review (did it match requirements?)
- Code quality review (security, performance, maintainability)
- Iterative fixes until approved

### The Security Vulnerability (400 words)

**How Code Review Saved My Ass**

During the code quality review of the UserPromptSubmit hook, the reviewer flagged this:

```bash
# VULNERABLE (original code):
suggestion = discovery.suggest_tool('''$PROMPT''')
```

Looks innocent. It's not.

**The Exploit:**

User prompt: `test'''; __import__('os').system('rm -rf /'); x='''test`

What happens:
1. Bash expands `$PROMPT` to the user input
2. Triple quotes close, malicious Python executes
3. Arbitrary code runs with my permissions
4. Complete system compromise

This is a **prompt injection vulnerability**. In a tool discovery system. That runs on every user prompt. Automatically.

Yeah.

**The Fix:**

```bash
# SECURE (fixed code):
suggestion = discovery.suggest_tool(sys.argv[1])
" "$PROMPT"
```

Pass the prompt as a command-line argument, not string interpolation. Python receives it as `sys.argv[1]`, never evaluates it as code.

**Lessons Learned:**

1. **Never trust user input** - Even in "internal" tools
2. **String interpolation is dangerous** - Especially in bash with triple quotes
3. **Code review is mandatory** - I wouldn't have caught this myself
4. **Test your exploits** - I verified the vulnerability before fixing it
5. **Security in development, not deployment** - Caught before production

The code quality reviewer also found:
- Database connection leak (no `close()` calls)
- Resource management issues (missing `finally` blocks)
- PID reuse edge case (24-hour state expiration needed)

All fixed before deployment. All caught by systematic review.

**This is why process matters.**

### The Results (300 words)

**What I Built:**

- **285 lines of Python** across 4 modules (database, scorer, session_start, realtime)
- **2 bash hooks** (SessionStart + UserPromptSubmit)
- **1 seed script** to populate registry with 10 tools
- **8 integration tests** (all passing)
- **613-line README** with comprehensive documentation

**Performance:**
- SessionStart: 106ms (well under 200ms budget)
- Real-time: <50ms (timeout enforced)
- Database queries: <10ms
- All tests: 0.09s total

**Security:**
- Prompt injection vulnerability: Fixed
- Resource leaks: Fixed
- All code reviewed and approved

**Uniqueness:**

I searched GitHub. Nobody else has:
- Memory + Tool Discovery + Hooks (combined)
- Conversation-driven suggestions
- Custom tool support (not just MCP)
- Dual-mode discovery (proactive + reactive)
- Zero external dependencies

Memory systems exist. Tool systems exist. But this combination? **First of its kind.**

**Impact:**

In the week since deployment:
- 10 tools actively suggested
- 3 tools I'd completely forgotten, now used daily
- Zero false positives (keyword matching is precise)
- Zero performance issues (hooks are fast)
- Zero session crashes (graceful degradation works)

The system does exactly what I needed: **remembers my tools so I don't have to**.

### How It Works (Technical Deep Dive) (500 words)

**For the developers who want to understand the internals:**

**Database Layer (database.py)**
- PostgreSQL connection using psycopg2
- Password from `.pgpass` (not hardcoded)
- Simple query: `SELECT title, content FROM reference_info WHERE category='tool'`
- Returns list of tool dicts with JSONB metadata
- Connection cleanup with `finally` blocks (learned this the hard way)

**Scoring Algorithm (scorer.py)**
- Tokenize conversation topics: `["distributed", "ai", "orchestration"]`
- Match against tool keywords: `["distributed", "cluster", "parallel"]`
- Scoring:
  - Exact match: +10 points
  - Partial match: +5 points
  - Recently used (7 days): +3 points
  - High usage (>10 uses): +2 points
- Sort by score, return top N

**SessionStart Discovery (session_start.py)**
1. Connect to `conversation_summaries` table
2. Query last 3 conversations for `topics_discussed`
3. Extract topics, pass to scorer
4. Get all tools from registry
5. Rank tools by relevance score
6. Format top 5 for output
7. If no topics: Fall back to most-used tools

**Real-time Detection (realtime.py)**
1. Check rate limit (message counter in `/tmp/tool-discovery-session.json`)
2. Scan prompt for regex patterns:
   - `r'multi-model|consensus'` → llm-council
   - `r'distributed|72b'` → kage-bunshin
   - `r'docker environment'` → docker-debugger
3. Look up tool in registry
4. Check duplicate prevention (already suggested?)
5. Format suggestion with emoji indicator
6. Update state file

**Hooks (bash wrappers)**

SessionStart hook:
```bash
#!/bin/bash
timeout 0.2s python3 -c "
import sys
sys.path.insert(0, '/home/ndninja/scripts')
from tool_discovery.session_start import SessionStartDiscovery

discovery = SessionStartDiscovery()
tools = discovery.get_relevant_tools(limit=5)
if tools:
    print(discovery.format_suggestions(tools))
" 2>>/home/ndninja/.logs/tool-discovery.log

exit 0  # Never block session start
```

Key features:
- **Timeout protection**: Hard 200ms limit
- **Graceful degradation**: Always exits 0
- **Error logging**: Stderr to log file
- **No blocking**: Session starts even if hook fails

UserPromptSubmit hook: Same pattern, 50ms timeout, uses `sys.argv[1]` for prompt

**Why This Architecture?**

- **Hooks**: Automatic, no manual trigger needed
- **Python modules**: Testable, maintainable, reusable
- **PostgreSQL**: Already running, JSONB flexible, fast queries
- **State files**: Simple persistence, no external services
- **Bash wrappers**: Timeout enforcement, error isolation

### Try It Yourself (200 words)

**Installation (5 minutes)**

1. **Clone the repo:**
   ```bash
   git clone https://github.com/AI-Prompt-Ops-Kitchen/ndninja-home.git
   cd ndninja-home
   ```

2. **Set up PostgreSQL:**
   - You need PostgreSQL with a `claude_memory` database
   - Create `.pgpass` file: `localhost:5432:*:claude_mcp:your_password`
   - Permissions: `chmod 600 ~/.pgpass`

3. **Seed the registry:**
   ```bash
   python3 scripts/tool_registry_seed.py
   ```
   This adds 10 example tools. Customize them for your setup!

4. **Install hooks:**
   ```bash
   cp .claude/hooks/on-session-start-tool-discovery.sh ~/.claude/hooks/
   cp .claude/hooks/on-user-prompt-tool-discovery.sh ~/.claude/hooks/
   chmod +x ~/.claude/hooks/on-*-tool-discovery.sh
   ```

5. **Start Claude Code:**
   ```bash
   claude
   ```
   You should see tool suggestions based on your recent conversations!

**Add Your Own Tools:**

Edit `scripts/tool_registry_seed.py` and add your custom tools with keywords. Re-run the seed script. Done!

### What's Next (300 words)

**Immediate Plans:**

**1. Analytics Dashboard**
- Track which tools get suggested most
- Monitor suggestion accuracy (did user engage?)
- Identify underutilized tools
- Measure time saved by suggestions

**2. Shared Tool Registry**
- Community-contributed tool definitions
- GitHub repo of common developer tools
- Easy import: `tool_registry import community/docker-tools.json`

**3. IDE Plugins**
- VS Code extension
- JetBrains plugin
- Cursor integration

**4. Smart Keyword Learning**
- Machine learning to improve keyword matching
- "You typed X and ignored the suggestion, learn from that"
- Adaptive scoring based on usage patterns

**Long-Term Vision:**

This is just the beginning. The real potential:

**Personal AI Memory Ecosystem:**
- Tools discovered based on conversation
- Workflows suggested based on patterns
- Code snippets surfaced at the right time
- Documentation links when you need them
- API endpoints when you're coding

Imagine: You start working on a React component. Before you even ask, Claude suggests:
- Your component library's Storybook
- The design system tokens file
- The last similar component you built
- The custom hook you wrote for this pattern
- The testing utilities you always use

**Memory-first development:** The AI remembers your entire ecosystem and proactively helps you leverage it.

That's the future I'm building toward.

### Join the Journey (150 words)

**This is open source.** I want your contributions.

**Add your tools:** What custom utilities have you built?
**Improve the algorithm:** Better scoring? Smarter matching?
**Build integrations:** VS Code? Vim? Cursor?
**Share your experience:** Did it work? What broke?

**GitHub:** [Link to repo]
**Substack:** Subscribe for updates on new features
**Issues/PRs:** I review everything

This started with forgetting my LLM Council. It's becoming a complete memory ecosystem for developers.

If you've ever built something useful and then forgotten it exists, **this is for you**.

If you think AI should remember your tools so you don't have to, **this is for you**.

If you want to join the journey from "I forgot my own tool" to "AI-powered development memory," **this is for you**.

Let's build it together.

---

## Substack-Specific Elements

### Email Newsletter Format
- **Subject Line**: "I built an AI that remembers my tools (so I don't have to)"
- **Preview Text**: "How I solved the 'I built this cool thing and completely forgot it exists' problem with conversation-driven tool discovery"
- **Opening Image**: Terminal screenshot showing tool suggestions
- **Call-to-Action Buttons**:
  - "Try it yourself (GitHub)"
  - "Subscribe for updates"
  - "Join the discussion (comments)"

### Subscription Pitch (End of Article)
"Want to follow this journey? I'm building a complete memory ecosystem for developers—tools, workflows, code patterns, all surfaced at exactly the right moment. Subscribe to get updates when I ship new features, share lessons learned, and explore the future of AI-assisted development."

### Discussion Prompts
- What custom tools have you built and forgotten?
- PostgreSQL vs Vector DBs for AI memory—what would you choose?
- Should tool discovery be opt-in or automatic?
- What other development workflows need AI memory?

---

## Promotion Strategy

### Substack Notes (Short-form)
1. "Just published: How I taught my AI to remember my custom tools" + link
2. "The security vulnerability that almost destroyed my system" + link to that section
3. "Nobody else has built this—here's why that's weird" + link
4. Poll: "Do you forget your own tools?" Yes/No/What tools?

### Cross-promotion
- Instagram: Visual snippets from article
- YouTube Shorts: Key concepts in 60 seconds
- LinkedIn: Professional angle (productivity, efficiency)

### SEO Keywords
- AI memory for developers
- Tool discovery automation
- Claude Code plugins
- Custom tool management
- Developer productivity tools
- Memory-assisted development

---

## Follow-up Articles

**Article 2**: "Building the Tool Registry: PostgreSQL vs Vector Databases"
**Article 3**: "Subagent-Driven Development: How I Built This in One Session"
**Article 4**: "The Security Review That Saved My System"
**Article 5**: "From 10 Tools to 100: Scaling the Memory System"

---

Ready to publish! 🚀

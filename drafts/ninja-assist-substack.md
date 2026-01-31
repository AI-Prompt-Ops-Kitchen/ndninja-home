# I Built an AI That Understands My ADHD Brain
*How Ninja Assist eliminates command-line cognitive overload*

---

## The Problem Nobody Talks About

I have ADHD and Autism. I love building with AI tools. But here's my dirty secret:

**I can never remember the commands.**

- Was it `gh pr create` or `git pr`?
- Which flag makes it verbose again?
- I KNOW I can do this, but my brain won't retrieve the syntax.

Every time I context-switch to look up a command, I lose 15 minutes. Sometimes I abandon the task entirely.

**This isn't a knowledge problem. It's an interface problem.**

---

## The "Just Google It" Fallacy

People say "just look it up." But for neurodivergent folks:

1. Looking it up = context switch
2. Context switch = lost working memory
3. Lost working memory = decision paralysis
4. Decision paralysis = task avoidance

What takes a neurotypical person 30 seconds takes me 20 minutes — or never happens at all.

---

## What If AI Could Just... Understand?

I wanted an AI layer that speaks my language:

| What I Say | What Happens |
|------------|--------------|
| "help me code a parser" | Routes to Claude Code |
| "research best databases" | Searches the web |
| "install numpy" | Runs `pip install numpy` |
| "what was I working on?" | Shows project context |

No flags. No syntax. No decision fatigue.

---

## Introducing Ninja Assist

I built it in a single Saturday morning session with my AI assistant (hi Clawd! 🐾).

**5 modules, 57 tests, zero commands to remember.**

### How It Works

```
Plain English → Pattern Matching → Right Tool
                    ↓
              (0 LLM tokens!)
```

The magic: **50+ regex patterns** that catch common requests *before* hitting the LLM. This means:
- Instant routing (no API latency)
- Zero token cost for 80%+ of requests
- Predictable behavior

### It Learns From Mistakes

When it gets something wrong, I tell it:
```
"That was wrong, I meant research"
```

It learns a new pattern. Next time, it gets it right.

---

## The Neurodivergent Design Principles

Everything in Ninja Assist follows these rules:

1. **No multi-step manual processes** — If it requires remembering steps, it will fail
2. **No command syntax** — Plain English or bust
3. **Proactive, not reactive** — It reminds ME, not the other way around
4. **Automation is non-negotiable** — Manual = failure points for ADHD

---

## The Numbers

After one day of use:
- **2,100 tokens saved** (~$0.02, but it adds up)
- **42 requests routed** without thinking about syntax
- **0 commands looked up**

More importantly: **0 tasks abandoned due to command-line friction.**

---

## Try It Yourself

It's open source: [github.com/AI-Prompt-Ops-Kitchen/ninja-assist](https://github.com/AI-Prompt-Ops-Kitchen/ninja-assist)

Works with any AI assistant that can run Python. Built for [Clawdbot](https://clawdbot.com) but portable.

---

## The Bigger Picture

We talk a lot about AI "alignment" — making AI do what humans want.

But what about **interface alignment**? Making AI work the way *our brains* work?

For neurodivergent people, the command line isn't just inconvenient. It's a barrier. Every flag we have to remember is cognitive load we could spend on actual work.

Ninja Assist isn't revolutionary technology. It's just... **kind design**.

And sometimes, that's enough.

---

*Built by [Neurodivergent Ninja](https://youtube.com/@NeurodivergentNinja) 🥷*

*Follow for more ADHD-friendly AI workflows.*

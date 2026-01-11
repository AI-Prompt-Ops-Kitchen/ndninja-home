---
name: verify-official
description: Verify claims against official sources with domain-first evidence capture
version: 1.0.2
category: verification
args: ["claim", "[--domains]", "[--save-to-craft]"]
when_to_use: "User needs to verify a factual claim, especially for content publishing. Prevents hallucination and fabricated citations by requiring official domain validation. Critical before publishing blog posts, articles, or documentation."
tags: [verification, fact-checking, hallucination-prevention, sources, publishing]
examples:
  - /verify-official "Claude Opus 4.5 was released in November 2025"
  - /verify-official "Diablo 4 Paladin class releases in April 2026" --domains=blizzard.com,diablo4.blizzard.com
  - /verify-official "React 19 supports Server Components" --save-to-craft
last_reflection: 2026-01-11
reflection_count: 0
---

# Verify Official Sources

**Purpose:** Verify factual claims using ONLY official, authoritative sources. Designed to prevent AI hallucination and fabricated citations by enforcing strict domain validation.

## Critical Rules

🚨 **NEVER accept information without official source verification**
🚨 **NEVER fabricate URLs or citations**
🚨 **NEVER trust secondary sources for primary facts**
🚨 **ALWAYS show exact URLs and quotes**

## Usage

```bash
/verify-official "claim to verify" [--domains] [--save-to-craft]
```

**Parameters:**
- `claim` (required): The factual statement to verify
- `--domains` (optional): Comma-separated list of official domains to check first
- `--save-to-craft` (optional): Save verification report to Craft for future reference

**Examples:**
```bash
/verify-official "Anthropic released Claude 3.5 Sonnet in June 2024"
/verify-official "Next.js 14 supports Server Actions" --domains=nextjs.org,vercel.com
/verify-official "PostgreSQL 16 added logical replication improvements" --save-to-craft
```

## Workflow

### Step 1: Parse the Claim

Extract key entities and facts from the claim:
- **Product/Technology:** What is being claimed about?
- **Company/Organization:** Who is the authoritative source?
- **Specific Fact:** What exactly is claimed? (release date, feature, version, etc.)
- **Temporal Context:** When did this allegedly happen/exist?

Example:
```
Claim: "Diablo 4 Paladin class releases in April 2026"

Entities:
- Product: Diablo 4
- Feature: Paladin class
- Company: Blizzard Entertainment
- Claimed Date: April 2026
- Official domains: blizzard.com, diablo4.blizzard.com, news.blizzard.com
```

### Step 2: Identify Official Domains

Determine authoritative sources BEFORE searching. Official domains must be:
- **Primary sources:** Company's own website, official blog, press releases
- **Government sources:** .gov domains for regulatory/legal information
- **Standards bodies:** W3C, IETF, ISO for technical standards

**Common Official Domain Patterns:**
- Tech companies: `company.com`, `blog.company.com`, `docs.company.com`
- Open source: `project.org`, `project.io`, GitHub official repos
- Standards: `w3.org`, `ietf.org`, `ecma-international.org`

**Example Official Domains by Company:**
- Anthropic: `anthropic.com`, `www.anthropic.com/news`
- Blizzard: `blizzard.com`, `news.blizzard.com`, `diablo4.blizzard.com`
- Meta/React: `react.dev`, `reactjs.org`, `github.com/facebook/react`
- Next.js: `nextjs.org`, `vercel.com/blog`
- PostgreSQL: `postgresql.org`, `www.postgresql.org/docs`

### Step 3: Search Official Sources

Use WebSearch with strict domain filtering:

```bash
# Search ONLY official domains
WebSearch: "{claim keywords} site:{official-domain}"
```

**Multi-Domain Search Strategy:**
```bash
# Try multiple official sources in order of authority:
1. WebSearch: "Paladin class April 2026 site:news.blizzard.com"
2. WebSearch: "Paladin class Lord of Hatred site:diablo4.blizzard.com"
3. WebSearch: "Diablo 4 expansion 2026 site:blizzard.com"
```

**⚠️ Warning Signs of Hallucination:**
- No results on official domains
- Only secondary sources (news sites, forums, Reddit) mention the claim
- Dates/details conflict between sources
- URLs in search results don't actually exist when visited
- Information appears in "AI overview" but not in actual source pages

### Step 4: Verify Source Content

For each potential source found:

1. **Fetch the actual page content:**
   ```bash
   WebFetch: "{url}" "Extract the exact text related to {claim}. Include publication date."
   ```

2. **Validate the information:**
   - ✅ Exact quote matches the claim
   - ✅ URL is from official domain
   - ✅ Publication date is reasonable/recent
   - ✅ Content is specific and detailed (not vague)

3. **Document the evidence:**
   ```markdown
   ### Evidence Found

   **Source:** [Official Title](https://exact-url-here)
   **Domain:** official-domain.com ✓
   **Published:** YYYY-MM-DD
   **Relevant Quote:**
   > "Exact quote from the page that supports or refutes the claim"

   **Status:** ✅ VERIFIED | ❌ REFUTED | ⚠️ PARTIALLY VERIFIED | ❓ UNVERIFIABLE
   ```

### Step 5: Handle Unverifiable Claims

If NO official sources confirm the claim after exhaustive search:

```markdown
## ⚠️ VERIFICATION FAILED

**Claim:** "{original claim}"

**Official Sources Checked:**
- ✗ company1.com - No results
- ✗ company2.com - No results
- ✗ official-blog.com - No results

**Secondary Sources Found:**
- news-site.com - Mentions claim but cites no official source
- reddit.com/r/community - User speculation only

**VERDICT:** ❌ UNVERIFIABLE - Do not publish or cite this claim

**Recommendation:**
Either:
1. Remove this claim from your content
2. Mark as "unconfirmed" or "rumored"
3. Wait for official announcement

**DO NOT fabricate sources or use AI-generated URLs**
```

### Step 6: Generate Verification Report

Create a structured report with all findings:

```markdown
# Verification Report: {claim}

**Date:** {current_date}
**Status:** {VERIFIED|REFUTED|UNVERIFIABLE}

## Claim Analyzed
"{original claim}"

## Official Sources

### Primary Evidence
1. **{Source Title}**
   - URL: {exact_url}
   - Domain: {domain} ✓ Official
   - Published: {date}
   - Quote: "{relevant_excerpt}"
   - Assessment: {supports|refutes|neutral}

2. **{Source Title 2}**
   - [Same structure...]

## Summary

{Concise verdict: Is the claim accurate? What's the evidence?}

## Recommendations

- ✅ Safe to publish: {why/why not}
- 📝 Suggested wording: "{how to phrase this accurately}"
- ⚠️ Caveats: {any important context or limitations}

## Citation Format

**Plain text:**
According to {Source Name} ({domain}, {date}), "{accurate quote}"

**Markdown:**
As stated in [{Source Name}]({url}), "{accurate quote}"

---
*Verified using /verify-official skill on {date}*
```

### Step 7: Optional - Save to Craft

If `--save-to-craft` flag is present:

```bash
# Save verification report to Craft in "Verifications" folder
craft_mcp: create_document(
  title="Verification: {short_claim_summary}",
  content="{verification_report_markdown}",
  folder="Verifications",
  tags=["verification", "fact-check", "{company_name}"]
)
```

## AuDHD-Friendly Features

**Reduce Anxiety About Accuracy:**
- Clear pass/fail verdicts (no ambiguity)
- Multiple source validation (not just trusting one result)
- Explicit "DO NOT PUBLISH" warnings when unverifiable
- Structured checklist format (not open-ended investigation)

**Executive Function Support:**
- Step-by-step workflow (no decision paralysis)
- Pre-defined official domain patterns
- Copy-paste ready citations
- Automatic report generation

**Hyperfocus Accommodation:**
- Can deep-dive into verification without losing track
- Saves all findings in structured format
- --save-to-craft creates permanent reference

## Real-World Examples

### Example 1: Successful Verification

**Input:**
```bash
/verify-official "Anthropic released Claude 3.5 Sonnet in June 2024"
```

**Output:**
```markdown
# Verification Report: Anthropic Claude 3.5 Sonnet Release

**Status:** ✅ VERIFIED

## Official Sources

1. **Introducing Claude 3.5 Sonnet**
   - URL: https://www.anthropic.com/news/claude-3-5-sonnet
   - Domain: anthropic.com ✓ Official
   - Published: June 20, 2024
   - Quote: "Today, we're announcing Claude 3.5 Sonnet, the first model in our Claude 3.5 family."

## Summary
VERIFIED: Anthropic did release Claude 3.5 Sonnet in June 2024 (specifically June 20, 2024).

✅ Safe to publish with citation
```

### Example 2: Failed Verification (Fabrication Detected)

**Input:**
```bash
/verify-official "Diablo 4 Paladin class releases in April 2026"
```

**Output:**
```markdown
# Verification Report: Diablo 4 Paladin Class April 2026

**Status:** ❌ UNVERIFIABLE - Possible AI Hallucination

## Official Sources Checked
- ✗ news.blizzard.com - No results for "Paladin April 2026"
- ✗ diablo4.blizzard.com - No Paladin announcement found
- ✗ blizzard.com - No Lord of Hatred expansion details

## Findings
No official Blizzard sources confirm:
- Paladin class for Diablo 4
- April 2026 release date
- "Lord of Hatred" expansion existence

## Warning Signs Detected
🚨 Information only appeared in AI search summaries
🚨 No direct official source URLs provided
🚨 Secondary sources cite each other, not Blizzard

## VERDICT
❌ DO NOT PUBLISH - This claim cannot be verified from official sources.

## Recommendation
Remove this claim entirely or mark as:
"According to unconfirmed reports..." (but better to just remove it)

**CRITICAL:** This appears to be an AI hallucination or fabricated information.
```

### Example 3: Partially Verified (Needs Clarification)

**Input:**
```bash
/verify-official "React 19 supports Server Components"
```

**Output:**
```markdown
# Verification Report: React 19 Server Components

**Status:** ⚠️ PARTIALLY VERIFIED - Needs Clarification

## Official Sources

1. **React 19 RC Announcement**
   - URL: https://react.dev/blog/2024/04/25/react-19
   - Domain: react.dev ✓ Official
   - Published: April 25, 2024
   - Quote: "React 19 RC includes support for Server Components"

## Clarification Needed

The claim is technically correct, but incomplete:
- React 19 supports Server Components ✅
- BUT: Server Components were introduced earlier (React 18)
- React 19 improves and stabilizes them (not introduces them)

## Recommended Accurate Phrasing

Instead of: "React 19 supports Server Components"
Use: "React 19 includes stable support for Server Components"
Or: "Server Components are fully supported in React 19"

✅ Safe to publish with corrected wording
```

## Edge Cases

**Multiple Conflicting Official Sources:**
```markdown
⚠️ CONFLICTING INFORMATION

Official Source A says: X
Official Source B says: Y

Investigation needed:
- Check publication dates (use more recent)
- Check source authority (press release > blog > forum)
- Contact company directly if critical
```

**Official Source Link is Broken/404:**
```markdown
⚠️ BROKEN OFFICIAL LINK

The official URL appears in search results but returns 404.

Actions:
1. Check Internet Archive: archive.org/web/
2. Search for updated URL on official domain
3. If unavailable, mark as "previously verified, link broken"
```

**Claim About Future Events:**
```markdown
ℹ️ FUTURE CLAIM

This claim is about a future event. Verification shows:
- Official announcement exists: ✅
- But actual event hasn't occurred yet

Mark as: "Scheduled for {date} according to official announcement"
Include: "Subject to change" disclaimer
```

## Integration with Other Skills

**Works well with:**
- `/blog-checklist` - Run verification before publishing
- `/generate-doc` - Verify facts in generated documentation
- `/track-action-items` - Create action item for verification failures

**Workflow Example:**
```bash
# 1. Generate blog post draft
/generate-doc "Blog post about new tech features"

# 2. Extract claims to verify
# (manually identify factual claims in draft)

# 3. Verify each claim
/verify-official "Claim 1 from blog post"
/verify-official "Claim 2 from blog post"

# 4. Update blog post with verified info + citations
# 5. Save verification reports for audit trail
```

## Success Criteria

A successful verification should:
1. ✅ Search official sources exhaustively
2. ✅ Provide exact URLs and quotes
3. ✅ Give clear verdict (verified/refuted/unverifiable)
4. ✅ Prevent fabricated citations from being published
5. ✅ Generate copy-paste ready citations

**Measurement:** Zero fabricated sources in published content that used this skill.

## Implementation Notes

### Tools Required
- `WebSearch` with site: operator support
- `WebFetch` for retrieving actual page content
- Optional: `mcp__craft__*` tools for --save-to-craft
- Optional: `mcp__claude-memory__save_reference` for storing verified sources

### Performance Optimization
- Cache official domain lists per company/topic
- Save verification reports to prevent redundant checks
- Build up a library of verified facts over time

### Privacy & Rate Limiting
- Respect robots.txt on official domains
- Don't hammer APIs (rate limit searches)
- Use cached results when claim is identical

## Future Enhancements (v2.0+)

- Auto-detect claims in text and prompt for verification
- Integration with citation managers (Zotero, etc.)
- Bulk verification mode for entire documents
- Confidence scoring (high/medium/low confidence in verdict)
- Visual diff showing claim vs. actual official statement
- Auto-update verification reports when official info changes

---

## 🧠 Learnings

_No learnings yet - skill needs real-world usage and feedback._

<!--
Note: Previous learning about "Contributor Covenant v2.1" was removed as it
was unrelated to verification workflow. This skill should learn about:
- Effective search patterns for official sources
- Domain patterns by company/technology
- Common verification pitfalls
-->

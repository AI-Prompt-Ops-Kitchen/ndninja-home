"""
Analyzer - Uses LLM Council to analyze signals and propose skill updates
"""

import json
import subprocess
from typing import List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path
from signal_detector import Signal
from config import SKILLS_DIR, LLM_COUNCIL_SCRIPT, COUNCIL_TIMEOUT


@dataclass
class Reflection:
    """Represents a proposed skill update"""
    skill_name: str
    signal_type: str
    signal_text: str
    confidence: str
    what_changed: str
    proposed_update: str
    source_session: str
    rationale: str = ""


class Analyzer:
    """Analyzes signals and proposes skill updates using LLM Council"""

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.council_script = LLM_COUNCIL_SCRIPT

    def analyze_with_council(self, signals: List[Signal]) -> List[Reflection]:
        """
        Analyzes signals with LLM Council for multi-model consensus.

        Args:
            signals: List of detected signals

        Returns:
            List of Reflection objects with proposed skill updates
        """
        if not signals:
            return []

        # Get list of available skills
        available_skills = self._get_available_skills()

        # Build analysis prompt
        prompt = self._build_analysis_prompt(signals, available_skills)

        # Run LLM Council
        council_response = self._run_council(prompt)

        # Parse reflections from council response
        reflections = self._parse_council_response(council_response, signals)

        return reflections

    def _get_available_skills(self) -> List[str]:
        """Get list of available skill files"""
        if not self.skills_dir.exists():
            return []

        skills = []
        for skill_file in self.skills_dir.glob('*.md'):
            skills.append(skill_file.stem)

        return sorted(skills)

    def _build_analysis_prompt(self, signals: List[Signal], available_skills: List[str]) -> str:
        """Build the analysis prompt for LLM Council"""

        # Convert signals to JSON for clarity
        signals_json = []
        for signal in signals:
            signals_json.append({
                'type': signal.signal_type,
                'text': signal.signal_text,
                'confidence': signal.confidence,
                'context': signal.context[:200],  # Truncate for brevity
                'session': signal.source_session,
                'occurrences': signal.occurrence_count
            })

        prompt = f"""You are analyzing correction signals from Claude Code conversations to determine which skills should be updated.

DETECTED SIGNALS:
{json.dumps(signals_json, indent=2)}

AVAILABLE SKILLS:
{', '.join(available_skills)}

Your task:
1. Determine which skill(s) should be updated based on each signal
2. Extract the specific learning (what was wrong, what's correct)
3. Assess confidence level for each reflection:
   - HIGH: Explicit correction, repeated 2+ times, or very clear preference
   - MEDIUM: Single clear correction, somewhat specific
   - LOW: Implied preference, vague, needs clarification

4. Propose specific changes to skill markdown files
5. Explain why this update matters (rationale)

IMPORTANT RULES:
- Only suggest updates for skills that actually exist in the available skills list
- If a signal doesn't clearly map to an existing skill, mark skill_name as "NEW_SKILL" with suggestion
- Be specific about what needs to change in the skill file
- Don't propose vague updates like "improve the skill" - be concrete
- Consider whether this is truly a generalizable learning or just a one-off correction

Return ONLY valid JSON (no markdown, no explanation text) in this format:
{{
  "reflections": [
    {{
      "skill_name": "verify-official",
      "signal_type": "correction",
      "signal_text": "Always use WebFetch to verify, not just WebSearch",
      "confidence": "high",
      "what_changed": "Added mandatory WebFetch verification step after WebSearch",
      "proposed_update": "Add new Step 4: Verify with WebFetch section that explains WebSearch can be stale",
      "source_session": "session-id-here",
      "rationale": "User explicitly corrected this behavior, indicating WebSearch alone is insufficient"
    }}
  ]
}}

If no actionable reflections can be derived from the signals, return:
{{
  "reflections": []
}}
"""

        return prompt

    def _run_council(self, prompt: str) -> str:
        """
        Run analysis with Claude API (simplified for Phase 1).

        Args:
            prompt: The analysis prompt

        Returns:
            JSON response
        """
        try:
            # Use Claude API for structured analysis
            # Note: LLM Council integration deferred to Phase 2
            import os

            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("Warning: ANTHROPIC_API_KEY not set, using fallback")
                return "{\"reflections\": []}"

            # Use anthropic package if available, otherwise curl
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no other text."
                    }]
                )

                return message.content[0].text

            except ImportError:
                # Fallback to curl
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no other text.")
                    prompt_file = f.name

                try:
                    result = subprocess.run([
                        'curl', '-s', 'https://api.anthropic.com/v1/messages',
                        '-H', 'content-type: application/json',
                        '-H', f'x-api-key: {api_key}',
                        '-H', 'anthropic-version: 2023-06-01',
                        '-d', json.dumps({
                            'model': 'claude-sonnet-4-20250514',
                            'max_tokens': 4096,
                            'messages': [{'role': 'user', 'content': open(prompt_file).read()}]
                        })
                    ], capture_output=True, text=True, timeout=COUNCIL_TIMEOUT)

                    os.unlink(prompt_file)

                    if result.returncode != 0:
                        print(f"Warning: API call failed: {result.stderr}")
                        return "{\"reflections\": []}"

                    response_data = json.loads(result.stdout)
                    return response_data['content'][0]['text']

                finally:
                    if os.path.exists(prompt_file):
                        os.unlink(prompt_file)

        except subprocess.TimeoutExpired:
            print(f"Warning: API call timed out after {COUNCIL_TIMEOUT}s")
            return "{\"reflections\": []}"
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return "{\"reflections\": []}"

    def _parse_council_response(self, response: str, signals: List[Signal]) -> List[Reflection]:
        """
        Parse LLM Council JSON response into Reflection objects.

        Args:
            response: Raw council response
            signals: Original signals (for fallback data)

        Returns:
            List of Reflection objects
        """
        try:
            # Try to extract JSON from response (council might add extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                print("Warning: No JSON found in council response")
                return []

            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            reflections = []
            for item in data.get('reflections', []):
                # Validate required fields
                required_fields = [
                    'skill_name', 'signal_type', 'signal_text',
                    'confidence', 'what_changed', 'proposed_update', 'source_session'
                ]

                if not all(field in item for field in required_fields):
                    print(f"Warning: Skipping incomplete reflection: {item}")
                    continue

                # Validate confidence level
                if item['confidence'] not in ['high', 'medium', 'low']:
                    item['confidence'] = 'medium'  # Default

                # Validate signal type
                if item['signal_type'] not in ['correction', 'pattern', 'preference']:
                    item['signal_type'] = 'correction'  # Default

                reflection = Reflection(
                    skill_name=item['skill_name'],
                    signal_type=item['signal_type'],
                    signal_text=item['signal_text'],
                    confidence=item['confidence'],
                    what_changed=item['what_changed'],
                    proposed_update=item['proposed_update'],
                    source_session=item['source_session'],
                    rationale=item.get('rationale', '')
                )

                reflections.append(reflection)

            return reflections

        except json.JSONDecodeError as e:
            print(f"Error parsing council response as JSON: {e}")
            print(f"Response was: {response[:500]}")
            return []
        except Exception as e:
            print(f"Error parsing council response: {e}")
            return []

    def analyze_single_signal(self, signal: Signal, skill_name: str) -> Reflection:
        """
        Simple analysis for a single signal targeting a specific skill.
        Bypasses LLM Council for simple cases.

        Args:
            signal: The signal to analyze
            skill_name: Target skill to update

        Returns:
            Reflection object
        """
        return Reflection(
            skill_name=skill_name,
            signal_type=signal.signal_type,
            signal_text=signal.signal_text,
            confidence=signal.confidence,
            what_changed=f"Updated based on: {signal.signal_text}",
            proposed_update=signal.signal_text,
            source_session=signal.source_session,
            rationale="Simple single-signal update"
        )

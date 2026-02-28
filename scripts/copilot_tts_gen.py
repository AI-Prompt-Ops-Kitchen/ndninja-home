#!/usr/bin/env python3
"""Generate per-section TTS audio for Copilot Explainer video."""
import sys
sys.path.insert(0, "/home/ndninja/scripts")
from ninja_content import generate_tts, get_audio_duration
import json

OUTPUT_DIR = "/home/ndninja/projects/remotion-video/public"
VOICE_ID = "aQspKon0UdKOuBZQQrEE"

# Per-section narration text (clean, no tags — calm style doesn't need them)
SECTIONS = {
    "title": "Copilot for Microsoft 365. Your beginner's quick reference guide.",

    "section1": (
        "Let's start with the basics. A prompt is simply the instruction or question "
        "you type into Copilot. Think of Copilot as a highly capable, lightning-fast "
        "digital assistant sitting right inside your Microsoft 365 apps. The clearer "
        "and more specific your instructions are, the better the work it hands back to you. "
        "Here's a good way to think about it. Asking a colleague to \"make a presentation\" "
        "gives you something generic. But asking them to \"create a ten-slide summary of "
        "Q4 sales results with charts comparing to Q3\" — that gets you exactly what you need. "
        "Copilot works the same way."
    ),

    "section2": (
        "So where do you actually use this day to day? Let's walk through the four most "
        "common use cases. "
        "First — summarization. You can say \"Summarize the key takeaways and action items "
        "from the Teams meeting I just attended.\" Copilot pulls from the meeting transcript "
        "and gives you a clean summary in seconds. "
        "Second — information retrieval. Try something like \"What were the main project "
        "updates discussed in my emails with the management team over the past week?\" "
        "Instead of digging through dozens of emails, Copilot surfaces what matters. "
        "Third — analysis. Ask it to \"Explain the impact of this recent CVE report in "
        "simple terms.\" It translates complex material into language anyone on your team "
        "can understand. "
        "And fourth — brainstorming. When you're stuck, try \"Give me five creative ideas "
        "for our upcoming department all-hands meeting.\" It's a great way to get past the "
        "blank page."
    ),

    "section3": (
        "Copilot is especially powerful when it comes to writing. It can draft, edit, and "
        "adjust the tone of your work across Word, Outlook, and Teams. "
        "For drafting, you might say \"Draft an email to the team summarizing the new Intune "
        "device policies, keeping the tone professional but encouraging.\" You get a solid "
        "first draft in seconds. "
        "For refining existing content, try \"Rewrite this technical documentation step by "
        "step so it's easy for a non-technical user to understand.\" Copilot adapts the "
        "language and structure for your audience. "
        "And for summarizing — \"Draft a half-page executive summary of this fifteen-page "
        "project proposal.\" It pulls out the most important points so your leadership gets "
        "the highlights without the deep dive."
    ),

    "section4": (
        "Here's a technique that dramatically improves your results — role-based prompting. "
        "The idea is simple: give Copilot a job title so it understands the perspective and "
        "expertise level you need. "
        "For example — \"Act as a senior IT systems administrator. Write a step-by-step "
        "troubleshooting guide for a user who cannot connect to the VPN.\" The response will "
        "include technical specifics and structured steps. "
        "Or try — \"Act as a customer success manager and draft a polite response to a client "
        "who is frustrated about a delayed project timeline.\" Now the response prioritizes "
        "empathy, clarity, and professionalism. "
        "Why does this work so well? When you assign a role, Copilot adjusts its vocabulary, "
        "assumptions, and level of detail to match that persona. It's one of the most effective "
        "prompting techniques you can learn."
    ),

    "section5": (
        "This is where Copilot becomes a true enterprise superpower. It's securely connected "
        "to your Microsoft 365 data — your files, emails, meetings, and chats. You can type "
        "the forward-slash symbol or use the paperclip icon to reference specific files "
        "directly in your prompt. "
        "For example — \"Draft a project update email based on the timeline in Project "
        "Roadmap dot docx.\" Copilot reads the file and generates a relevant update based on "
        "your actual data. "
        "And an important note on security — Copilot respects your existing Microsoft 365 "
        "permissions. It can only access files and data that you already have access to. "
        "Your data stays within your organization's security boundary."
    ),

    "section6": (
        "Let's close with two pro tips that will take your Copilot skills to the next level. "
        "First — the meta-prompt. If you're not getting the answer you want, or you don't "
        "know where to start, let Copilot help you write the prompt. Tell it your goal, and "
        "ask it to interview you. For example — \"I need to write a PowerShell script to "
        "automate a task, but I'm not sure how to prompt you for it. Before you write anything, "
        "please ask me any clarifying questions you need to do this job perfectly.\" "
        "Second — embrace iteration. Your first prompt rarely produces a perfect result. "
        "Treat Copilot like a conversation. If the email it drafts is too long, just reply — "
        "\"Make it shorter and more casual.\" Or \"Add bullet points for the key action items.\" "
        "Or \"Change the tone to be more formal.\" Each revision builds on the previous one. "
        "Keep tweaking until it's right."
    ),

    "outro": (
        "Copilot for Microsoft 365. Start simple, iterate often, and let AI handle the "
        "heavy lifting."
    ),
}

def main():
    durations = {}
    for name, text in SECTIONS.items():
        output_path = f"{OUTPUT_DIR}/copilot_{name}.mp3"
        print(f"\n{'='*60}")
        print(f"Generating: {name} ({len(text)} chars)")
        print(f"{'='*60}")
        result = generate_tts(text, output_path, voice_id=VOICE_ID,
                              pad_start=0.3, voice_style="calm")
        if result:
            dur = get_audio_duration(output_path)
            durations[name] = round(dur, 2)
            print(f"   Duration: {dur:.2f}s")
        else:
            print(f"   FAILED!")
            return

    # Write timing manifest for Remotion
    manifest_path = f"{OUTPUT_DIR}/copilot_timing.json"
    with open(manifest_path, "w") as f:
        json.dump(durations, f, indent=2)
    print(f"\n{'='*60}")
    print(f"TIMING MANIFEST: {manifest_path}")
    print(json.dumps(durations, indent=2))
    total = sum(durations.values())
    print(f"Total duration: {total:.2f}s ({total/60:.1f} min)")

if __name__ == "__main__":
    main()

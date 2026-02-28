import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/* ───────── colour tokens (matching PDF palette) ───────── */
const TEAL = "#0891B2";
const TEAL_LIGHT = "#E0F7FA";
const TEAL_DARK = "#0E7490";
const BLUE = "#3B82F6";
const BLUE_LIGHT = "#EFF6FF";
const GREEN = "#059669";
const GREEN_LIGHT = "#ECFDF5";
const AMBER = "#D97706";
const AMBER_LIGHT = "#FFFBEB";
const PURPLE = "#7C3AED";
const PURPLE_LIGHT = "#F5F3FF";
const GRAY_50 = "#F9FAFB";
const GRAY_700 = "#374151";
const GRAY_900 = "#111827";

/* ───────── timing (frames at 30fps) ───────── */
const FPS = 30;
const sec = (s: number) => Math.round(s * FPS);

// Audio durations from TTS manifest
const DUR = {
  title: 5.43,
  section1: 35.71,
  section2: 53.0,
  section3: 40.46,
  section4: 46.37,
  section5: 40.86,
  section6: 50.31,
  outro: 8.15,
};

// Section start times (cumulative) + 0.5s gap between sections
const GAP = 0.5;
const START = {
  title: 0,
  section1: DUR.title + GAP,
  section2: DUR.title + GAP + DUR.section1 + GAP,
  section3: DUR.title + GAP + DUR.section1 + GAP + DUR.section2 + GAP,
  section4:
    DUR.title +
    GAP +
    DUR.section1 +
    GAP +
    DUR.section2 +
    GAP +
    DUR.section3 +
    GAP,
  section5:
    DUR.title +
    GAP +
    DUR.section1 +
    GAP +
    DUR.section2 +
    GAP +
    DUR.section3 +
    GAP +
    DUR.section4 +
    GAP,
  section6:
    DUR.title +
    GAP +
    DUR.section1 +
    GAP +
    DUR.section2 +
    GAP +
    DUR.section3 +
    GAP +
    DUR.section4 +
    GAP +
    DUR.section5 +
    GAP,
  outro:
    DUR.title +
    GAP +
    DUR.section1 +
    GAP +
    DUR.section2 +
    GAP +
    DUR.section3 +
    GAP +
    DUR.section4 +
    GAP +
    DUR.section5 +
    GAP +
    DUR.section6 +
    GAP,
};

const TOTAL_DUR =
  START.outro + DUR.outro + 2; // +2s fade-out
export const TOTAL_FRAMES = sec(TOTAL_DUR);

/* ───────── section data ───────── */
interface SectionData {
  num: number;
  title: string;
  color: string;
  colorLight: string;
  image: string;
  audio: string;
  startSec: number;
  durSec: number;
  bullets?: string[];
  examples?: { label: string; text: string; cardColor: string }[];
  callout?: { title: string; text: string };
}

const SECTIONS: SectionData[] = [
  {
    num: 1,
    title: "What is a Prompt?",
    color: TEAL,
    colorLight: TEAL_LIGHT,
    image: "nb2_section1_prompt.png",
    audio: "copilot_section1.mp3",
    startSec: START.section1,
    durSec: DUR.section1,
    bullets: [
      "Instruction or question you type into Copilot",
      "Clearer instructions → better results",
    ],
    callout: {
      title: "Think of it like this:",
      text: '"Create a 10-slide Q4 sales summary with charts" beats "make a presentation"',
    },
  },
  {
    num: 2,
    title: "Top Everyday Use Cases",
    color: BLUE,
    colorLight: BLUE_LIGHT,
    image: "nb2_section2_usecases.png",
    audio: "copilot_section2.mp3",
    startSec: START.section2,
    durSec: DUR.section2,
    examples: [
      {
        label: "Summarization",
        text: '"Summarize the key takeaways from my Teams meeting"',
        cardColor: TEAL,
      },
      {
        label: "Information Retrieval",
        text: '"What were the main project updates in my emails this week?"',
        cardColor: BLUE,
      },
      {
        label: "Analysis",
        text: '"Explain this CVE report in simple terms"',
        cardColor: GREEN,
      },
      {
        label: "Brainstorming",
        text: '"Give me 5 ideas for our department all-hands"',
        cardColor: AMBER,
      },
    ],
  },
  {
    num: 3,
    title: "Writing Assistance",
    color: GREEN,
    colorLight: GREEN_LIGHT,
    image: "nb2_section3_writing.png",
    audio: "copilot_section3.mp3",
    startSec: START.section3,
    durSec: DUR.section3,
    examples: [
      {
        label: "Drafting",
        text: '"Draft an email summarizing Intune policies — professional but encouraging"',
        cardColor: TEAL,
      },
      {
        label: "Refining",
        text: '"Rewrite this documentation so non-technical users can follow"',
        cardColor: BLUE,
      },
      {
        label: "Summarizing",
        text: '"Draft a half-page executive summary of this 15-page proposal"',
        cardColor: GREEN,
      },
    ],
  },
  {
    num: 4,
    title: "Role-Based Prompting",
    color: AMBER,
    colorLight: AMBER_LIGHT,
    image: "nb2_section4_roles.png",
    audio: "copilot_section4.mp3",
    startSec: START.section4,
    durSec: DUR.section4,
    examples: [
      {
        label: "IT Administrator",
        text: '"Act as a senior IT admin. Write a VPN troubleshooting guide."',
        cardColor: AMBER,
      },
      {
        label: "Customer Success",
        text: '"Act as a CSM and draft a response to a frustrated client."',
        cardColor: PURPLE,
      },
    ],
    callout: {
      title: "Why does this work?",
      text: "Copilot adjusts vocabulary, assumptions and detail level to match the assigned role.",
    },
  },
  {
    num: 5,
    title: "Grounding Your Data",
    color: PURPLE,
    colorLight: PURPLE_LIGHT,
    image: "nb2_section5_grounding.png",
    audio: "copilot_section5.mp3",
    startSec: START.section5,
    durSec: DUR.section5,
    bullets: [
      "Use / or 📎 to reference files directly in prompts",
      "Copilot reads your actual Microsoft 365 data",
    ],
    examples: [
      {
        label: "File Reference",
        text: '"Draft a project update based on /Project_Roadmap.docx"',
        cardColor: PURPLE,
      },
    ],
    callout: {
      title: "Security Note",
      text: "Copilot respects your existing M365 permissions — it only accesses what you can access.",
    },
  },
  {
    num: 6,
    title: "Pro Tips: Meta-Prompt & Iteration",
    color: TEAL,
    colorLight: TEAL_LIGHT,
    image: "nb2_section6_iteration.png",
    audio: "copilot_section6.mp3",
    startSec: START.section6,
    durSec: DUR.section6,
    bullets: [
      'Meta-Prompt: "Ask me clarifying questions before you write anything"',
      "Iterate: your first prompt rarely produces perfection",
      '"Make it shorter" → "Add bullet points" → "More formal"',
    ],
  },
];

/* ───────── helper components ───────── */

function FadeIn({
  children,
  frame,
  delay = 0,
  duration = 15,
}: {
  children: React.ReactNode;
  frame: number;
  delay?: number;
  duration?: number;
}) {
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(frame, [delay, delay + duration], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{ opacity, transform: `translateY(${y}px)` }}>{children}</div>
  );
}

function SectionBadge({
  num,
  color,
  frame,
}: {
  num: number;
  color: string;
  frame: number;
}) {
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 200 } });
  return (
    <div
      style={{
        width: 56,
        height: 56,
        borderRadius: "50%",
        background: color,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "white",
        fontSize: 28,
        fontWeight: 700,
        transform: `scale(${scale})`,
        flexShrink: 0,
      }}
    >
      {num}
    </div>
  );
}

function ExampleCard({
  label,
  text,
  cardColor,
  frame,
  delay,
}: {
  label: string;
  text: string;
  cardColor: string;
  frame: number;
  delay: number;
}) {
  const opacity = interpolate(frame, [delay, delay + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x = interpolate(frame, [delay, delay + 12], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        opacity,
        transform: `translateX(${x}px)`,
        background: "white",
        borderLeft: `5px solid ${cardColor}`,
        borderRadius: 10,
        padding: "14px 18px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          textTransform: "uppercase" as const,
          letterSpacing: 1,
          color: cardColor,
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 17, color: GRAY_700, fontStyle: "italic", lineHeight: 1.5 }}>
        {text}
      </div>
    </div>
  );
}

function CalloutBox({
  title,
  text,
  color,
  frame,
  delay,
}: {
  title: string;
  text: string;
  color: string;
  frame: number;
  delay: number;
}) {
  const opacity = interpolate(frame, [delay, delay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        opacity,
        background: "white",
        border: `2px solid ${color}`,
        borderRadius: 12,
        padding: "16px 20px",
        marginTop: 16,
      }}
    >
      <div style={{ fontSize: 17, fontWeight: 700, color, marginBottom: 6 }}>
        {title}
      </div>
      <div style={{ fontSize: 16, color: GRAY_700, lineHeight: 1.6 }}>{text}</div>
    </div>
  );
}

/* ───────── section scene ───────── */

function SectionScene({ data }: { data: SectionData }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in / fade out for the entire section
  const sectionFrames = sec(data.durSec);
  const fadeOutStart = sectionFrames - 20;
  const opacity = interpolate(
    frame,
    [0, 15, fadeOutStart, sectionFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        opacity,
        background: `linear-gradient(160deg, ${data.colorLight} 0%, #FFFFFF 40%, #FFFFFF 100%)`,
        padding: "60px 80px",
        fontFamily:
          "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* Section header */}
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 30 }}>
        <SectionBadge num={data.num} color={data.color} frame={frame} />
        <FadeIn frame={frame} delay={5} duration={12}>
          <h2 style={{ fontSize: 42, fontWeight: 700, color: GRAY_900, margin: 0 }}>
            {data.title}
          </h2>
        </FadeIn>
      </div>

      <div style={{ display: "flex", gap: 40, flex: 1 }}>
        {/* Left: illustration */}
        <FadeIn frame={frame} delay={15} duration={18}>
          <div
            style={{
              width: 460,
              flexShrink: 0,
              borderRadius: 16,
              overflow: "hidden",
              background: GRAY_50,
              boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
            }}
          >
            <Img
              src={staticFile(data.image)}
              style={{ width: "100%", height: "auto", display: "block" }}
            />
          </div>
        </FadeIn>

        {/* Right: content */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Bullets */}
          {data.bullets?.map((b, i) => (
            <FadeIn key={i} frame={frame} delay={30 + i * 15} duration={12}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: data.color,
                    marginTop: 8,
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: 22, color: GRAY_700, lineHeight: 1.6 }}>{b}</span>
              </div>
            </FadeIn>
          ))}

          {/* Example cards */}
          {data.examples && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  data.examples.length > 2 ? "1fr 1fr" : "1fr",
                gap: 14,
              }}
            >
              {data.examples.map((ex, i) => (
                <ExampleCard
                  key={i}
                  label={ex.label}
                  text={ex.text}
                  cardColor={ex.cardColor}
                  frame={frame}
                  delay={30 + i * 18}
                />
              ))}
            </div>
          )}

          {/* Callout */}
          {data.callout && (
            <CalloutBox
              title={data.callout.title}
              text={data.callout.text}
              color={data.color}
              frame={frame}
              delay={sec(data.durSec * 0.55)}
            />
          )}
        </div>
      </div>

      {/* Bottom accent bar */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 4,
          background: data.color,
        }}
      />
    </AbsoluteFill>
  );
}

/* ───────── title card ───────── */

function TitleCard() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const titleFrames = sec(DUR.title + GAP);

  const opacity = interpolate(
    frame,
    [0, 15, titleFrames - 15, titleFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 150, mass: 0.8 },
  });

  return (
    <AbsoluteFill
      style={{
        opacity,
        background: `linear-gradient(135deg, ${TEAL} 0%, ${TEAL_DARK} 100%)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily:
          "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <div style={{ transform: `scale(${titleScale})`, textAlign: "center" }}>
        <h1
          style={{
            fontSize: 72,
            fontWeight: 700,
            color: "white",
            margin: 0,
            letterSpacing: -1,
          }}
        >
          Copilot for Microsoft 365
        </h1>
        <FadeIn frame={frame} delay={12} duration={15}>
          <p
            style={{
              fontSize: 32,
              color: "rgba(255,255,255,0.9)",
              marginTop: 16,
              fontWeight: 400,
            }}
          >
            Beginner&apos;s Quick Reference Guide
          </p>
        </FadeIn>
      </div>
    </AbsoluteFill>
  );
}

/* ───────── outro card ───────── */

function OutroCard() {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        opacity,
        background: `linear-gradient(135deg, ${TEAL} 0%, ${TEAL_DARK} 100%)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily:
          "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <FadeIn frame={frame} delay={5} duration={20}>
        <h2 style={{ fontSize: 48, color: "white", fontWeight: 700, textAlign: "center" }}>
          Start simple. Iterate often.
        </h2>
      </FadeIn>
      <FadeIn frame={frame} delay={20} duration={20}>
        <p
          style={{
            fontSize: 28,
            color: "rgba(255,255,255,0.85)",
            marginTop: 20,
            textAlign: "center",
          }}
        >
          Let AI handle the heavy lifting.
        </p>
      </FadeIn>
      <FadeIn frame={frame} delay={40} duration={15}>
        <p
          style={{
            fontSize: 18,
            color: "rgba(255,255,255,0.5)",
            marginTop: 60,
          }}
        >
          Copilot for Microsoft 365 — Internal Training Material — 2026
        </p>
      </FadeIn>
    </AbsoluteFill>
  );
}

/* ───────── main composition ───────── */

export interface CopilotExplainerProps {
  withMusic: boolean;
}

export const defaultCopilotProps: CopilotExplainerProps = {
  withMusic: false,
};

export const CopilotExplainer: React.FC<CopilotExplainerProps> = ({
  withMusic,
}) => {
  return (
    <AbsoluteFill style={{ background: "#FFFFFF" }}>
      {/* ── Audio layers ── */}
      <Sequence from={sec(START.title)} durationInFrames={sec(DUR.title)}>
        <Audio src={staticFile("copilot_title.mp3")} volume={1.0} />
      </Sequence>
      {SECTIONS.map((s) => (
        <Sequence
          key={s.num}
          from={sec(s.startSec)}
          durationInFrames={sec(s.durSec)}
        >
          <Audio src={staticFile(s.audio)} volume={1.0} />
        </Sequence>
      ))}
      <Sequence from={sec(START.outro)} durationInFrames={sec(DUR.outro)}>
        <Audio src={staticFile("copilot_outro.mp3")} volume={1.0} />
      </Sequence>

      {/* Background music (optional) */}
      {withMusic && (
        <Audio src={staticFile("calm_professional_flow.mp3")} volume={0.12} />
      )}

      {/* ── Visual layers ── */}
      {/* Title card */}
      <Sequence from={0} durationInFrames={sec(DUR.title + GAP)}>
        <TitleCard />
      </Sequence>

      {/* 6 content sections */}
      {SECTIONS.map((s) => (
        <Sequence
          key={s.num}
          from={sec(s.startSec)}
          durationInFrames={sec(s.durSec)}
        >
          <SectionScene data={s} />
        </Sequence>
      ))}

      {/* Outro */}
      <Sequence from={sec(START.outro)} durationInFrames={sec(DUR.outro + 2)}>
        <OutroCard />
      </Sequence>
    </AbsoluteFill>
  );
};

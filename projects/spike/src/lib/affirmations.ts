// Gentle affirmations after logging a spike
// These acknowledge the effort of tracking during distress
// No toxic positivity — just honest, kind recognition

const AFFIRMATIONS = [
  "You noticed it. That's the hardest part.",
  "Logged. Your future self will thank you.",
  "That took courage during a hard moment.",
  "Data point captured. You're building a picture.",
  "Feelings logged, not judged.",
  "Small act, big self-awareness.",
  "Your doctor will see this. You're advocating for yourself.",
  "Tracked. Now breathe.",
  "This information matters. You matter.",
  "One more data point toward understanding yourself.",
  "You didn't have to do this. But you did.",
  "Pattern recognition starts with moments like this.",
];

let lastIndex = -1;

export function getAffirmation(): string {
  // Avoid repeating the same one twice in a row
  let index: number;
  do {
    index = Math.floor(Math.random() * AFFIRMATIONS.length);
  } while (index === lastIndex && AFFIRMATIONS.length > 1);
  lastIndex = index;
  return AFFIRMATIONS[index];
}

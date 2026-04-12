// types.ts — Shared types for the Remotion short-video pipeline

export interface Section {
  type: "title" | "disclaimer" | "rating" | "point" | "comparison"
       | "data-highlight" | "catalyst" | "quote" | "risk-matrix"
       | "conclusion" | "follow";
  headline: string;
  body: string;
  tts_text: string;
  highlights?: string[];
  index?: number;
  sub_body?: string;
  metrics?: Metric[];
  // comparison
  bull_points?: string[];
  bear_points?: string[];
  verdict?: "bull" | "bear" | "neutral";
  // data-highlight
  value?: string;
  context?: string;
  signal?: "positive" | "negative" | "neutral";
  // catalyst
  events?: CatalystEvent[];
  // quote
  quote_text?: string;
  attribution?: string;
  // risk-matrix
  scenarios?: RiskScenario[];
}

export interface Metric {
  label: string;
  value: string;
  signal: "positive" | "negative" | "neutral";
}

export interface CatalystEvent {
  date: string;
  event: string;
}

export interface RiskScenario {
  label: string;
  probability: string;
  target: string;
  return: string;
  signal: "positive" | "negative" | "neutral";
}

export interface Timestamp {
  text: string;
  offset_ms: number;
  duration_ms: number;
}

export interface VideoProps {
  sections: Section[];
  timestamps: Timestamp[];
  audioPath: string;
  totalDuration: number;
  seed: string;
}

export interface SectionTiming {
  type: string;
  startFrame: number;
  durationFrames: number;
}

export interface ThemeVariant {
  hueShift: number;
  gradientAngle: number;
  orbs: OrbConfig[];
  fontWeight: 700 | 800 | 900;
  cardRadius: number;
  cardPadding: number;
  transitions: string[];
  springDamping: number;
  staggerDelay: number;
}

export interface OrbConfig {
  x: number;
  y: number;
  size: number;
  blur: number;
  hue: number;
  seed: number;
}

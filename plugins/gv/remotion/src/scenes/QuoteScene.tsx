import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { AnimatedText } from "../components/AnimatedText";
import { ProgressBar } from "../components/ProgressBar";
import type { Section, ThemeVariant } from "../types";
import { BASE_COLORS, rotateHue } from "../theme/colors";

interface Props {
  section: Section;
  variant: ThemeVariant;
  progressPct: number;
  progressIcon: string;
  ticker: string;
  date: string;
}

export const QuoteScene: React.FC<Props> = ({
  section,
  variant,
  progressPct,
  progressIcon,
  ticker,
  date,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const quoteMarkScale = spring({
    frame,
    fps,
    config: { damping: 10, mass: 0.8 },
  });

  // Split quote text by sentence-ending punctuation
  const quoteText = section.quote_text ?? section.body;
  const quoteLines = quoteText
    ? quoteText.split(/(?<=[。！？])/).filter((l) => l.trim())
    : [];

  const attrOpacity = interpolate(
    frame - Math.round(2.0 * fps),
    [0, 15],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const bg1 = rotateHue(BASE_COLORS.bgPrimary, variant.hueShift);
  const bg2 = rotateHue(BASE_COLORS.bgSecondary, variant.hueShift);

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: "relative",
        overflow: "hidden",
        background: `linear-gradient(${variant.gradientAngle}deg, ${bg1}, ${bg2})`,
        fontFamily: "'Noto Sans SC', sans-serif",
      }}
    >
      <FloatingOrbs orbs={variant.orbs} hueShift={variant.hueShift} />

      {/* Content */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        {/* Big opening quotation mark */}
        <div
          style={{
            fontSize: 200,
            fontWeight: 900,
            color: BASE_COLORS.accentPurple,
            opacity: 0.4,
            transform: `scale(${quoteMarkScale})`,
            lineHeight: 0.8,
            marginBottom: 24,
          }}
        >
          "
        </div>

        {/* Quote lines with typewriter */}
        <div
          style={{
            textAlign: "center",
            maxWidth: 850,
          }}
        >
          {quoteLines.map((line, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <AnimatedText
                text={line}
                effect="typewriter"
                enterDelay={0.5 + i * 0.3}
                style={{
                  fontSize: 40,
                  fontWeight: 700,
                  color: BASE_COLORS.textPrimary,
                  lineHeight: 1.6,
                }}
              />
            </div>
          ))}
        </div>

        {/* Attribution */}
        {section.attribution && (
          <div
            style={{
              marginTop: 48,
              opacity: attrOpacity,
              fontSize: 28,
              color: BASE_COLORS.textSecondary,
              fontStyle: "italic",
            }}
          >
            — {section.attribution}
          </div>
        )}
      </div>

      {/* Progress bar */}
      <ProgressBar progress={progressPct} icon={progressIcon} />

      {/* Brand bar */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: 80,
          right: 80,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: 28, fontWeight: 700, color: BASE_COLORS.textPrimary }}>
          {ticker}
        </span>
        <span style={{ fontSize: 24, color: BASE_COLORS.textSecondary }}>
          {date}
        </span>
      </div>

      <FilmGrain />
    </div>
  );
};

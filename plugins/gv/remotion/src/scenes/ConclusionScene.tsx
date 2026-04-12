import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { AnimatedText } from "../components/AnimatedText";
import { HighlightChip } from "../components/HighlightChip";
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

export const ConclusionScene: React.FC<Props> = ({
  section,
  variant,
  progressPct,
  progressIcon,
  ticker,
  date,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const decoSpring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const decoWidth = interpolate(decoSpring, [0, 1], [0, 120]);

  const labelOpacity = interpolate(frame, [24, 39], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const bodyOpacity = interpolate(
    frame - Math.round(2.5 * fps),
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
        {/* Decorative line top */}
        <div
          style={{
            width: decoWidth,
            height: 3,
            background: `linear-gradient(90deg, ${BASE_COLORS.accentPurple}, ${BASE_COLORS.accentBlue})`,
            borderRadius: 2,
            marginBottom: 32,
          }}
        />

        {/* Label */}
        <div
          style={{
            fontSize: 30,
            fontWeight: 600,
            color: BASE_COLORS.textSecondary,
            opacity: labelOpacity,
            letterSpacing: 6,
            marginBottom: 40,
          }}
        >
          结论
        </div>

        {/* Headline with blur-in */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <AnimatedText
            text={section.headline}
            effect="blur-in"
            enterDelay={1.2}
            damping={variant.springDamping}
            style={{
              fontSize: 56,
              fontWeight: variant.fontWeight,
              color: BASE_COLORS.textPrimary,
              lineHeight: 1.3,
            }}
          />
        </div>

        {/* Highlight chips */}
        {section.highlights && section.highlights.length > 0 && (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: 12,
              marginBottom: 32,
            }}
          >
            {section.highlights.map((chip, i) => (
              <HighlightChip key={i} text={chip} index={i} enterDelay={2.0} />
            ))}
          </div>
        )}

        {/* Body text */}
        <p
          style={{
            fontSize: 32,
            color: BASE_COLORS.textSecondary,
            opacity: bodyOpacity,
            lineHeight: 1.8,
            textAlign: "center",
            maxWidth: 800,
          }}
        >
          {section.body}
        </p>

        {/* Decorative line bottom */}
        <div
          style={{
            width: decoWidth,
            height: 3,
            background: `linear-gradient(90deg, ${BASE_COLORS.accentBlue}, ${BASE_COLORS.accentPurple})`,
            borderRadius: 2,
            marginTop: 40,
          }}
        />
      </div>

      {/* Progress bar at 100% */}
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

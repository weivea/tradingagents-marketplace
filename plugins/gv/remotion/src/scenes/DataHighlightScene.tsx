import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { CountUp } from "../components/CountUp";
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

export const DataHighlightScene: React.FC<Props> = ({
  section,
  variant,
  progressPct,
  progressIcon,
  ticker,
  date,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const labelOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 0.8 Hz glow pulse
  const glowPhase = Math.sin(t * Math.PI * 2 * 0.8);
  const glowIntensity = interpolate(glowPhase, [-1, 1], [0.3, 0.8]);

  const contextOpacity = interpolate(
    frame - Math.round(1.8 * fps),
    [0, 15],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const signalColor =
    section.signal === "positive"
      ? BASE_COLORS.ratingBuy
      : section.signal === "negative"
        ? BASE_COLORS.ratingSell
        : BASE_COLORS.ratingHold;

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
        {/* Label */}
        <div
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: BASE_COLORS.textSecondary,
            opacity: labelOpacity,
            letterSpacing: 4,
            marginBottom: 48,
          }}
        >
          {section.headline}
        </div>

        {/* Big data number */}
        <div
          style={{
            textShadow: `0 0 ${60 * glowIntensity}px ${signalColor}`,
            marginBottom: 48,
          }}
        >
          <CountUp
            value={section.value ?? "0"}
            startDelay={0.3}
            duration={1.5}
            style={{
              fontSize: 120,
              fontWeight: 900,
              color: signalColor,
            }}
          />
        </div>

        {/* Context text */}
        {section.context && (
          <p
            style={{
              fontSize: 32,
              color: BASE_COLORS.textSecondary,
              opacity: contextOpacity,
              lineHeight: 1.8,
              textAlign: "center",
              maxWidth: 800,
            }}
          >
            {section.context}
          </p>
        )}

        {/* Body text */}
        {section.body && (
          <p
            style={{
              fontSize: 28,
              color: BASE_COLORS.textSecondary,
              opacity: contextOpacity,
              lineHeight: 1.6,
              textAlign: "center",
              maxWidth: 800,
              marginTop: 24,
            }}
          >
            {section.body}
          </p>
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

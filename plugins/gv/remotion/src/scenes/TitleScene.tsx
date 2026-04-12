import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { AnimatedText } from "../components/AnimatedText";
import type { Section, ThemeVariant } from "../types";
import { BASE_COLORS, rotateHue } from "../theme/colors";

interface Props {
  section: Section;
  variant: ThemeVariant;
  ticker: string;
  date: string;
}

export const TitleScene: React.FC<Props> = ({ section, variant, ticker, date }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const gridProgress = spring({
    frame: Math.max(0, frame - 9),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });

  const decoSpring = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const decoWidth = interpolate(decoSpring, [0, 1], [0, 120]);

  const titleProgress = spring({
    frame: Math.max(0, frame - 45),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const titleY = interpolate(titleProgress, [0, 1], [60, 0]);

  const dateOpacity = interpolate(frame, [66, 81], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const brandOpacity = interpolate(frame, [90, 105], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

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
        opacity: bgOpacity,
        fontFamily: "'Noto Sans SC', sans-serif",
      }}
    >
      <FloatingOrbs orbs={variant.orbs} hueShift={variant.hueShift} />

      {/* Grid lines */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            width: 800,
            height: 800,
            border: "1px solid rgba(255,255,255,0.05)",
            transform: `scale(${gridProgress})`,
            opacity: 0.3,
          }}
        />
      </div>

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
        {/* Decorative lines */}
        <div
          style={{
            width: decoWidth,
            height: 3,
            background: `linear-gradient(90deg, ${BASE_COLORS.accentPurple}, ${BASE_COLORS.accentBlue})`,
            borderRadius: 2,
            marginBottom: 40,
          }}
        />

        {/* Label */}
        <AnimatedText
          text="今日交易研报"
          effect="typewriter"
          enterDelay={0.9}
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: BASE_COLORS.textSecondary,
            letterSpacing: 8,
            marginBottom: 32,
          }}
        />

        {/* Headline */}
        <div
          style={{
            opacity: titleProgress,
            transform: `translateY(${titleY}px)`,
            textAlign: "center",
          }}
        >
          <h1
            style={{
              fontSize: 72,
              fontWeight: variant.fontWeight,
              color: BASE_COLORS.textPrimary,
              lineHeight: 1.2,
              margin: 0,
            }}
          >
            {section.headline}
          </h1>
        </div>

        {/* Date */}
        <div
          style={{
            opacity: dateOpacity,
            marginTop: 48,
            fontSize: 32,
            color: BASE_COLORS.textSecondary,
          }}
        >
          {date}
        </div>

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
          opacity: brandOpacity,
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

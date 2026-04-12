import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { GlassCard } from "../components/GlassCard";
import { HighlightChip } from "../components/HighlightChip";
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

function getRatingColor(headline: string): string {
  if (/买入|增持/.test(headline)) return BASE_COLORS.ratingBuy;
  if (/卖出|减持/.test(headline)) return BASE_COLORS.ratingSell;
  return BASE_COLORS.ratingHold;
}

export const RatingScene: React.FC<Props> = ({
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

  const labelOpacity = interpolate(frame, [9, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const ratingScale = spring({
    frame: Math.max(0, frame - 30),
    fps,
    config: { damping: 8, mass: 0.8 },
  });

  // 0.5 Hz glow pulse
  const glowPhase = Math.sin(t * Math.PI * 2 * 0.5);
  const glowIntensity = interpolate(glowPhase, [-1, 1], [0.3, 0.8]);

  const bodyOpacity = interpolate(frame, [75, 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const ratingColor = getRatingColor(section.headline);
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
        <GlassCard
          radius={variant.cardRadius}
          padding={variant.cardPadding}
          enterDelay={0.3}
          damping={variant.springDamping}
          style={{ width: "100%", textAlign: "center" }}
        >
          {/* Label */}
          <div
            style={{
              fontSize: 30,
              color: BASE_COLORS.textSecondary,
              opacity: labelOpacity,
              marginBottom: 24,
              letterSpacing: 4,
            }}
          >
            投资评级
          </div>

          {/* Rating text */}
          <div
            style={{
              fontSize: 96,
              fontWeight: variant.fontWeight,
              color: ratingColor,
              transform: `scale(${ratingScale})`,
              textShadow: `0 0 ${40 * glowIntensity}px ${ratingColor}`,
              marginBottom: 32,
            }}
          >
            {section.headline}
          </div>

          {/* Highlight chips */}
          {section.highlights && section.highlights.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                justifyContent: "center",
                gap: 12,
                marginBottom: 24,
              }}
            >
              {section.highlights.map((chip, i) => (
                <HighlightChip key={i} text={chip} index={i} enterDelay={1.8} />
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
              marginBottom: 32,
            }}
          >
            {section.body}
          </p>

          {/* Metrics grid */}
          {section.metrics && section.metrics.length > 0 && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: 20,
              }}
            >
              {section.metrics.map((m, i) => {
                const metricDelay = 3.0 + i * 0.2;
                const metricOpacity = interpolate(
                  frame - Math.round(metricDelay * fps),
                  [0, 15],
                  [0, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                );
                const signalColor =
                  m.signal === "positive"
                    ? BASE_COLORS.ratingBuy
                    : m.signal === "negative"
                      ? BASE_COLORS.ratingSell
                      : BASE_COLORS.textSecondary;

                return (
                  <div
                    key={i}
                    style={{
                      opacity: metricOpacity,
                      textAlign: "center",
                      padding: 16,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 24,
                        color: BASE_COLORS.textSecondary,
                        marginBottom: 8,
                      }}
                    >
                      {m.label}
                    </div>
                    <CountUp
                      value={m.value}
                      startDelay={metricDelay}
                      style={{
                        fontSize: 40,
                        fontWeight: 700,
                        color: signalColor,
                      }}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
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

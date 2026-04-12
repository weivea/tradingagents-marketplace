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
  enterDirection?: "left" | "right";
}

export const PointScene: React.FC<Props> = ({
  section,
  variant,
  progressPct,
  progressIcon,
  ticker,
  date,
  enterDirection = "left",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const indexScale = spring({
    frame,
    fps,
    config: { damping: 8, mass: 0.8 },
  });

  const decoSpring = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const decoWidth = interpolate(decoSpring, [0, 1], [0, 120]);

  const headlineOpacity = interpolate(frame, [24, 39], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Split body by Chinese punctuation
  const bodyLines = section.body
    ? section.body.split(/(?<=[。；！？，])/)
    : [];

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
        {/* Numbered circle */}
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            background: `linear-gradient(135deg, ${BASE_COLORS.accentPurple}, ${BASE_COLORS.accentBlue})`,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontSize: 40,
            fontWeight: 900,
            color: "#fff",
            transform: `scale(${indexScale})`,
            marginBottom: 32,
          }}
        >
          {section.index ?? 1}
        </div>

        <GlassCard
          radius={variant.cardRadius}
          padding={variant.cardPadding}
          enterDelay={0.5}
          enterFrom={enterDirection}
          damping={variant.springDamping}
          style={{ width: "100%" }}
        >
          {/* Decorative line */}
          <div
            style={{
              width: decoWidth,
              height: 3,
              background: `linear-gradient(90deg, ${BASE_COLORS.accentPurple}, ${BASE_COLORS.accentBlue})`,
              borderRadius: 2,
              marginBottom: 24,
            }}
          />

          {/* Headline */}
          <h2
            style={{
              fontSize: 48,
              fontWeight: variant.fontWeight,
              color: BASE_COLORS.textPrimary,
              opacity: headlineOpacity,
              lineHeight: 1.3,
              marginBottom: 24,
            }}
          >
            {section.headline}
          </h2>

          {/* Highlight chips */}
          {section.highlights && section.highlights.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 12,
                marginBottom: 24,
              }}
            >
              {section.highlights.map((chip, i) => (
                <HighlightChip key={i} text={chip} index={i} enterDelay={1.5} />
              ))}
            </div>
          )}

          {/* Staggered body lines */}
          <div style={{ marginBottom: 24 }}>
            {bodyLines.map((line, i) => {
              const lineDelay = 1.8 + i * variant.staggerDelay;
              const lineOpacity = interpolate(
                frame - Math.round(lineDelay * fps),
                [0, 15],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
              );
              return (
                <p
                  key={i}
                  style={{
                    fontSize: 30,
                    color: BASE_COLORS.textSecondary,
                    opacity: lineOpacity,
                    lineHeight: 1.8,
                    margin: "4px 0",
                  }}
                >
                  {line}
                </p>
              );
            })}
          </div>

          {/* Sub body */}
          {section.sub_body && (
            <p
              style={{
                fontSize: 26,
                color: BASE_COLORS.textSecondary,
                opacity: interpolate(
                  frame - Math.round(2.5 * fps),
                  [0, 15],
                  [0, 0.8],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                ),
                lineHeight: 1.6,
                marginBottom: 24,
                fontStyle: "italic",
              }}
            >
              {section.sub_body}
            </p>
          )}

          {/* Metrics */}
          {section.metrics && section.metrics.length > 0 && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: 16,
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
                      padding: 12,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 22,
                        color: BASE_COLORS.textSecondary,
                        marginBottom: 6,
                      }}
                    >
                      {m.label}
                    </div>
                    <CountUp
                      value={m.value}
                      startDelay={metricDelay}
                      style={{
                        fontSize: 36,
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

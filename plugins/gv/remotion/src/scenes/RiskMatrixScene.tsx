import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
import { GlassCard } from "../components/GlassCard";
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

export const RiskMatrixScene: React.FC<Props> = ({
  section,
  variant,
  progressPct,
  progressIcon,
  ticker,
  date,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const scenarios = section.scenarios ?? [];
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
        {/* Title */}
        <h2
          style={{
            fontSize: 44,
            fontWeight: variant.fontWeight,
            color: BASE_COLORS.textPrimary,
            textAlign: "center",
            marginBottom: 40,
            opacity: titleOpacity,
          }}
        >
          {section.headline}
        </h2>

        {/* Scenario cards */}
        <div style={{ width: "100%", maxWidth: 920, display: "flex", flexDirection: "column", gap: 16 }}>
          {scenarios.map((scenario, i) => {
            const cardDelay = 0.5 + i * 0.4;
            const cardProgress = spring({
              frame: Math.max(0, frame - Math.round(cardDelay * fps)),
              fps,
              config: { damping: variant.springDamping, mass: 0.8 },
            });

            const signalColor =
              scenario.signal === "positive"
                ? BASE_COLORS.ratingBuy
                : scenario.signal === "negative"
                  ? BASE_COLORS.ratingSell
                  : BASE_COLORS.ratingHold;

            const borderColor =
              scenario.signal === "positive"
                ? "rgba(74, 222, 128, 0.3)"
                : scenario.signal === "negative"
                  ? "rgba(248, 113, 113, 0.3)"
                  : "rgba(251, 191, 36, 0.3)";

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 20,
                  background: "rgba(255, 255, 255, 0.06)",
                  border: `1px solid ${borderColor}`,
                  borderRadius: variant.cardRadius,
                  padding: "20px 28px",
                  opacity: cardProgress,
                  transform: `translateY(${interpolate(cardProgress, [0, 1], [30, 0])}px)`,
                }}
              >
                {/* Label */}
                <div style={{ flex: 2 }}>
                  <div
                    style={{
                      fontSize: 28,
                      fontWeight: 700,
                      color: BASE_COLORS.textPrimary,
                      marginBottom: 4,
                    }}
                  >
                    {scenario.label}
                  </div>
                  <div style={{ fontSize: 22, color: BASE_COLORS.textSecondary }}>
                    {scenario.target}
                  </div>
                </div>

                {/* Probability */}
                <div style={{ flex: 1, textAlign: "center" }}>
                  <div style={{ fontSize: 20, color: BASE_COLORS.textSecondary, marginBottom: 4 }}>
                    概率
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 700, color: signalColor }}>
                    {scenario.probability}
                  </div>
                </div>

                {/* Return */}
                <div style={{ flex: 1, textAlign: "center" }}>
                  <div style={{ fontSize: 20, color: BASE_COLORS.textSecondary, marginBottom: 4 }}>
                    回报
                  </div>
                  <div style={{ fontSize: 32, fontWeight: 700, color: signalColor }}>
                    {scenario.return}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Body text */}
        {section.body && (
          <p
            style={{
              fontSize: 28,
              color: BASE_COLORS.textSecondary,
              lineHeight: 1.6,
              textAlign: "center",
              maxWidth: 800,
              marginTop: 32,
              opacity: interpolate(
                frame - Math.round((0.5 + scenarios.length * 0.4 + 0.5) * fps),
                [0, 15],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
              ),
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

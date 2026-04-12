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

export const ComparisonScene: React.FC<Props> = ({
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

  const bullSlide = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const bullX = interpolate(bullSlide, [0, 1], [-100, 0]);

  const bearSlide = spring({
    frame: Math.max(0, frame - 24),
    fps,
    config: { damping: variant.springDamping, mass: 0.8 },
  });
  const bearX = interpolate(bearSlide, [0, 1], [100, 0]);

  const isBullish = section.verdict === "bull";
  const isBearish = section.verdict === "bear";

  const bullBorderOpacity = isBullish ? 0.5 : 0.15;
  const bearBorderOpacity = isBearish ? 0.5 : 0.15;

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
          padding: 60,
        }}
      >
        {/* Title */}
        <h2
          style={{
            fontSize: 48,
            fontWeight: variant.fontWeight,
            color: BASE_COLORS.textPrimary,
            opacity: titleOpacity,
            marginBottom: 40,
            textAlign: "center",
          }}
        >
          {section.headline}
        </h2>

        {/* Two panels side by side */}
        <div
          style={{
            display: "flex",
            gap: 24,
            width: "100%",
          }}
        >
          {/* Bull panel */}
          <div
            style={{
              flex: 1,
              opacity: bullSlide,
              transform: `translateX(${bullX}px)`,
            }}
          >
            <GlassCard
              radius={variant.cardRadius}
              padding={variant.cardPadding}
              enterDelay={0}
              style={{
                borderColor: `rgba(74, 222, 128, ${bullBorderOpacity})`,
                border: `2px solid rgba(74, 222, 128, ${bullBorderOpacity})`,
                height: "100%",
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: BASE_COLORS.ratingBuy,
                  marginBottom: 24,
                  textAlign: "center",
                }}
              >
                🐂 看多
              </div>
              {(section.bull_points ?? []).map((point, i) => {
                const pointDelay = 1.2 + i * variant.staggerDelay;
                const pointOpacity = interpolate(
                  frame - Math.round(pointDelay * fps),
                  [0, 15],
                  [0, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                );
                return (
                  <div
                    key={i}
                    style={{
                      fontSize: 28,
                      color: BASE_COLORS.textPrimary,
                      opacity: pointOpacity,
                      lineHeight: 1.6,
                      marginBottom: 12,
                      paddingLeft: 16,
                      borderLeft: `3px solid ${BASE_COLORS.ratingBuy}`,
                    }}
                  >
                    {point}
                  </div>
                );
              })}
            </GlassCard>
          </div>

          {/* Bear panel */}
          <div
            style={{
              flex: 1,
              opacity: bearSlide,
              transform: `translateX(${bearX}px)`,
            }}
          >
            <GlassCard
              radius={variant.cardRadius}
              padding={variant.cardPadding}
              enterDelay={0}
              style={{
                borderColor: `rgba(248, 113, 113, ${bearBorderOpacity})`,
                border: `2px solid rgba(248, 113, 113, ${bearBorderOpacity})`,
                height: "100%",
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: BASE_COLORS.ratingSell,
                  marginBottom: 24,
                  textAlign: "center",
                }}
              >
                🐻 看空
              </div>
              {(section.bear_points ?? []).map((point, i) => {
                const pointDelay = 2.0 + i * variant.staggerDelay;
                const pointOpacity = interpolate(
                  frame - Math.round(pointDelay * fps),
                  [0, 15],
                  [0, 1],
                  { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                );
                return (
                  <div
                    key={i}
                    style={{
                      fontSize: 28,
                      color: BASE_COLORS.textPrimary,
                      opacity: pointOpacity,
                      lineHeight: 1.6,
                      marginBottom: 12,
                      paddingLeft: 16,
                      borderLeft: `3px solid ${BASE_COLORS.ratingSell}`,
                    }}
                  >
                    {point}
                  </div>
                );
              })}
            </GlassCard>
          </div>
        </div>

        {/* Verdict */}
        {section.verdict && (
          <div
            style={{
              marginTop: 32,
              fontSize: 32,
              fontWeight: 700,
              color:
                section.verdict === "bull"
                  ? BASE_COLORS.ratingBuy
                  : section.verdict === "bear"
                    ? BASE_COLORS.ratingSell
                    : BASE_COLORS.ratingHold,
              opacity: interpolate(frame, [90, 105], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              textAlign: "center",
            }}
          >
            {section.body}
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

import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { FloatingOrbs } from "../components/FloatingOrbs";
import { FilmGrain } from "../components/FilmGrain";
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

const NODE_COLORS = ["#a855f7", "#3b82f6", "#4ade80"];

export const CatalystScene: React.FC<Props> = ({
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

  // Axis line draws from 0.5s to 1.5s
  const axisStart = Math.round(0.5 * fps);
  const axisEnd = Math.round(1.5 * fps);
  const axisProgress = interpolate(frame, [axisStart, axisEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const events = section.events ?? [];

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
          padding: 80,
          paddingTop: 200,
        }}
      >
        {/* Title */}
        <h2
          style={{
            fontSize: 48,
            fontWeight: variant.fontWeight,
            color: BASE_COLORS.textPrimary,
            opacity: titleOpacity,
            marginBottom: 60,
            textAlign: "center",
          }}
        >
          {section.headline}
        </h2>

        {/* Timeline container */}
        <div style={{ position: "relative", flex: 1, paddingLeft: 60 }}>
          {/* Vertical axis line */}
          <div
            style={{
              position: "absolute",
              left: 20,
              top: 0,
              width: 3,
              height: `${axisProgress * 100}%`,
              background: `linear-gradient(180deg, ${BASE_COLORS.accentPurple}, ${BASE_COLORS.accentBlue})`,
              borderRadius: 2,
            }}
          />

          {/* Event nodes */}
          {events.map((event, i) => {
            const nodeDelay = 1.0 + i * 0.8;
            const nodeScale = spring({
              frame: Math.max(0, frame - Math.round(nodeDelay * fps)),
              fps,
              config: { damping: 10, mass: 0.6 },
            });

            const textDelay = nodeDelay + 0.3;
            const textOpacity = interpolate(
              frame - Math.round(textDelay * fps),
              [0, 15],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );

            const color = NODE_COLORS[i % NODE_COLORS.length];

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  marginBottom: 48,
                  position: "relative",
                }}
              >
                {/* Node dot */}
                <div
                  style={{
                    position: "absolute",
                    left: -52,
                    top: 8,
                    width: 20,
                    height: 20,
                    borderRadius: "50%",
                    background: color,
                    transform: `scale(${nodeScale})`,
                    boxShadow: `0 0 16px ${color}`,
                  }}
                />

                {/* Event text */}
                <div style={{ opacity: textOpacity }}>
                  <div
                    style={{
                      fontSize: 26,
                      fontWeight: 700,
                      color,
                      marginBottom: 8,
                    }}
                  >
                    {event.date}
                  </div>
                  <div
                    style={{
                      fontSize: 30,
                      color: BASE_COLORS.textPrimary,
                      lineHeight: 1.5,
                    }}
                  >
                    {event.event}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
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

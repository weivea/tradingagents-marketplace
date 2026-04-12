import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

interface Props {
  children: React.ReactNode;
  radius?: number;
  padding?: number;
  enterDelay?: number;
  enterFrom?: "bottom" | "left" | "right" | "scale";
  damping?: number;
  style?: React.CSSProperties;
}

export const GlassCard: React.FC<Props> = ({
  children,
  radius = 24,
  padding = 40,
  enterDelay = 0,
  enterFrom = "bottom",
  damping = 12,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delayFrames = Math.round(enterDelay * fps);

  const progress = spring({
    frame: Math.max(0, frame - delayFrames),
    fps,
    config: { damping, mass: 0.8 },
  });

  let transform = "";
  if (enterFrom === "bottom") {
    const y = interpolate(progress, [0, 1], [60, 0]);
    transform = `translateY(${y}px)`;
  } else if (enterFrom === "left") {
    const x = interpolate(progress, [0, 1], [-100, 0]);
    transform = `translateX(${x}px)`;
  } else if (enterFrom === "right") {
    const x = interpolate(progress, [0, 1], [100, 0]);
    transform = `translateX(${x}px)`;
  } else {
    const s = interpolate(progress, [0, 1], [0.8, 1]);
    transform = `scale(${s})`;
  }

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.08)",
        border: "1px solid rgba(255, 255, 255, 0.12)",
        borderRadius: radius,
        padding,
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        opacity: progress,
        transform,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

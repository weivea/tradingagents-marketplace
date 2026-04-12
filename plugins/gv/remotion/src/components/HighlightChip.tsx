import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";

interface Props {
  text: string;
  index: number;
  staggerDelay?: number;
  enterDelay?: number;
}

export const HighlightChip: React.FC<Props> = ({
  text,
  index,
  staggerDelay = 0.15,
  enterDelay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delay = Math.round((enterDelay + index * staggerDelay) * fps);

  const progress = spring({
    frame: Math.max(0, frame - delay),
    fps,
    config: { damping: 12, mass: 0.6 },
  });

  const isNegative = text.startsWith("-");
  const isPositive = text.startsWith("+") || text.startsWith("$");

  const bgColor = isNegative
    ? "linear-gradient(135deg, rgba(255,68,68,0.2), rgba(255,68,68,0.1))"
    : isPositive
      ? "linear-gradient(135deg, rgba(74,222,128,0.2), rgba(74,222,128,0.1))"
      : "linear-gradient(135deg, rgba(100,108,255,0.2), rgba(59,130,246,0.2))";

  const borderColor = isNegative
    ? "rgba(255,68,68,0.3)"
    : isPositive
      ? "rgba(74,222,128,0.3)"
      : "rgba(100,108,255,0.3)";

  const textColor = isNegative ? "#f87171" : isPositive ? "#4ade80" : "#f1f5f9";

  return (
    <div
      style={{
        background: bgColor,
        border: `1px solid ${borderColor}`,
        borderRadius: 12,
        padding: "12px 24px",
        fontSize: 36,
        fontWeight: 700,
        color: textColor,
        opacity: progress,
        transform: `scale(${progress})`,
      }}
    >
      {text}
    </div>
  );
};

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface Props {
  value: string;
  startDelay?: number;
  duration?: number;
  style?: React.CSSProperties;
}

export const CountUp: React.FC<Props> = ({
  value,
  startDelay = 0,
  duration = 1.2,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delayFrames = Math.round(startDelay * fps);
  const durationFrames = Math.round(duration * fps);

  const match = value.match(/([+-]?)(\$?)(\d+\.?\d*)(.*)/);
  if (!match) return <span style={style}>{value}</span>;

  const [, sign, prefix, numStr, suffix] = match;
  const target = parseFloat(numStr);
  const hasDecimal = numStr.includes(".");
  const decimalPlaces = hasDecimal ? (numStr.split(".")[1]?.length ?? 0) : 0;

  const progress = interpolate(
    frame - delayFrames,
    [0, durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const eased = 1 - Math.pow(1 - progress, 3);
  const current = target * eased;
  const display = `${sign}${prefix}${current.toFixed(decimalPlaces)}${suffix}`;

  return <span style={style}>{display}</span>;
};

import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

interface Props {
  text: string;
  enterDelay?: number;
  effect?: "fade" | "typewriter" | "blur-in" | "spring-up";
  damping?: number;
  style?: React.CSSProperties;
}

export const AnimatedText: React.FC<Props> = ({
  text,
  enterDelay = 0,
  effect = "fade",
  damping = 12,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delayFrames = Math.round(enterDelay * fps);
  const localFrame = Math.max(0, frame - delayFrames);

  if (effect === "typewriter") {
    const charsPerSecond = 12;
    const visibleChars = Math.floor((localFrame / fps) * charsPerSecond);
    const displayed = text.slice(0, Math.min(visibleChars, text.length));
    const opacity = localFrame > 0 ? 1 : 0;
    return <span style={{ ...style, opacity }}>{displayed}</span>;
  }

  if (effect === "blur-in") {
    const progress = spring({ frame: localFrame, fps, config: { damping, mass: 0.8 } });
    const blur = interpolate(progress, [0, 1], [20, 0]);
    const scale = interpolate(progress, [0, 1], [1.1, 1]);
    return (
      <span style={{ ...style, opacity: progress, filter: `blur(${blur}px)`, transform: `scale(${scale})`, display: "inline-block" }}>
        {text}
      </span>
    );
  }

  if (effect === "spring-up") {
    const progress = spring({ frame: localFrame, fps, config: { damping, mass: 0.8 } });
    const y = interpolate(progress, [0, 1], [40, 0]);
    return (
      <span style={{ ...style, opacity: progress, transform: `translateY(${y}px)`, display: "inline-block" }}>
        {text}
      </span>
    );
  }

  const opacity = interpolate(localFrame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  return <span style={{ ...style, opacity }}>{text}</span>;
};

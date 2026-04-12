import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { Timestamp } from "../types";

interface Props {
  timestamps: Timestamp[];
  globalStartFrame: number;
}

export const Subtitle: React.FC<Props> = ({ timestamps, globalStartFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const globalFrame = globalStartFrame + frame;
  const currentMs = (globalFrame / fps) * 1000;

  const active = timestamps.find(
    (ts) => currentMs >= ts.offset_ms && currentMs < ts.offset_ms + ts.duration_ms,
  );

  if (!active) return null;

  const maxChars = 20;
  const text = active.text;
  const lines: string[] = [];
  let current = "";
  const breakable = new Set("，。；：！？、");
  for (const char of text) {
    current += char;
    if (current.length >= maxChars) {
      lines.push(current);
      current = "";
    } else if (breakable.has(char) && current.length >= 8) {
      lines.push(current);
      current = "";
    }
  }
  if (current) lines.push(current);

  return (
    <div
      style={{
        position: "absolute",
        bottom: "25%",
        left: 40,
        right: 40,
        textAlign: "center",
        pointerEvents: "none",
      }}
    >
      {lines.map((line, i) => (
        <div
          key={i}
          style={{
            fontSize: 42,
            fontWeight: 400,
            color: "#FFD400",
            textShadow: "0 0 8px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.6)",
            lineHeight: 1.6,
            fontFamily: "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
          }}
        >
          {line}
        </div>
      ))}
    </div>
  );
};

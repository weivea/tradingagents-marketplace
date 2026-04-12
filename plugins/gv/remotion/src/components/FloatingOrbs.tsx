import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { noise2D } from "../utils/noise";
import type { OrbConfig } from "../types";

interface Props {
  orbs: OrbConfig[];
  hueShift: number;
}

export const FloatingOrbs: React.FC<Props> = ({ orbs, hueShift }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
      {orbs.map((orb, i) => {
        const speed = 0.15;
        const dx = noise2D(t * speed, i * 100, orb.seed) * 0.1;
        const dy = noise2D(i * 100, t * speed, orb.seed + 1) * 0.1;
        const cx = (orb.x + dx) * width;
        const cy = (orb.y + dy) * height;

        const breathCycle = 3 + (orb.seed % 3);
        const breathScale = 1 + 0.1 * Math.sin((t * Math.PI * 2) / breathCycle);
        const size = orb.size * breathScale;

        const hue = (orb.hue + hueShift + 360) % 360;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: cx - size / 2,
              top: cy - size / 2,
              width: size,
              height: size,
              borderRadius: "50%",
              background: `radial-gradient(circle, hsla(${hue}, 70%, 60%, 0.35), transparent 70%)`,
              filter: `blur(${orb.blur}px)`,
            }}
          />
        );
      })}
    </div>
  );
};

import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";

export const FilmGrain: React.FC<{ opacity?: number }> = ({ opacity = 0.03 }) => {
  const frame = useCurrentFrame();
  const grainSeed = Math.floor(frame / 2);

  const svgFilter = useMemo(() => {
    return `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' seed='${grainSeed}'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E")`;
  }, [grainSeed]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: svgFilter,
        backgroundSize: "200px 200px",
        opacity,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    />
  );
};

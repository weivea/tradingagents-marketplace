import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";

/**
 * Film grain + dither overlay.
 *
 * Serves two purposes:
 * 1. **Anti-banding dither**: high-frequency noise injected at low opacity
 *    breaks up visible color steps in dark CSS gradients (the main cause of
 *    gradient banding in rendered video).
 * 2. **Film grain aesthetic**: gives the video a subtle organic texture.
 *
 * Uses `mixBlendMode: "normal"` (not "overlay") because overlay mode is
 * effectively invisible on dark backgrounds (overlay = 2*bg*fg when bg < 0.5).
 * A higher baseFrequency (0.9) produces finer noise that acts as dithering
 * without being perceptible as a pattern.
 */
export const FilmGrain: React.FC<{ opacity?: number }> = ({
  opacity = 0.12,
}) => {
  const frame = useCurrentFrame();

  // Re-seed every frame for temporal variation (no frozen pattern)
  const svgFilter = useMemo(() => {
    return `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' seed='${frame}'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E")`;
  }, [frame]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: svgFilter,
        backgroundSize: "256px 256px",
        opacity,
        mixBlendMode: "normal",
        pointerEvents: "none",
      }}
    />
  );
};

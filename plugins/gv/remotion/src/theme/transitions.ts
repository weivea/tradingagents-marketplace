import React from "react";

type TransitionType = "fade-through" | "slide-left" | "zoom-dissolve" | "wipe-up" | "morph-blur";

export function getTransitionStyles(
  type: TransitionType,
  progress: number,
  direction: "out" | "in",
): React.CSSProperties {
  switch (type) {
    case "fade-through":
      return {
        opacity: direction === "out" ? 1 - progress : progress,
      };
    case "slide-left":
      if (direction === "out") {
        return { transform: `translateX(${-progress * 100}%)`, opacity: 1 - progress };
      }
      return { transform: `translateX(${(1 - progress) * 100}%)`, opacity: progress };
    case "zoom-dissolve":
      if (direction === "out") {
        return {
          transform: `scale(${1 + progress * 0.3})`,
          filter: `blur(${progress * 10}px)`,
          opacity: 1 - progress,
        };
      }
      return {
        transform: `scale(${0.8 + progress * 0.2})`,
        opacity: progress,
      };
    case "wipe-up":
      if (direction === "out") {
        return { opacity: 1 - progress };
      }
      return {
        clipPath: `inset(${(1 - progress) * 100}% 0 0 0)`,
        opacity: 1,
      };
    case "morph-blur":
      if (direction === "out") {
        return { filter: `blur(${progress * 15}px)`, opacity: 1 - progress };
      }
      return { filter: `blur(${(1 - progress) * 15}px)`, opacity: progress };
    default:
      return { opacity: direction === "out" ? 1 - progress : progress };
  }
}

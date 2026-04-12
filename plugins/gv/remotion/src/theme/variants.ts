import { SeededRandom } from "../utils/seeded-random";
import type { ThemeVariant, OrbConfig } from "../types";

const GRADIENT_ANGLES = [120, 135, 150, 160, 180];
const FONT_WEIGHTS = [700, 800, 900] as const;
const CARD_RADII = [16, 20, 24];
const TRANSITION_POOL = [
  "fade-through",
  "slide-left",
  "zoom-dissolve",
  "wipe-up",
  "morph-blur",
];

export function generateVariant(seed: string): ThemeVariant {
  const rng = new SeededRandom(seed);

  const orbCount = rng.int(3, 5);
  const orbs: OrbConfig[] = Array.from({ length: orbCount }, () => ({
    x: rng.range(0.05, 0.95),
    y: rng.range(0.05, 0.95),
    size: rng.range(60, 150),
    blur: rng.range(20, 40),
    hue: rng.range(0, 360),
    seed: rng.int(0, 99999),
  }));

  return {
    hueShift: rng.range(-30, 30),
    gradientAngle: rng.pick(GRADIENT_ANGLES),
    orbs,
    fontWeight: rng.pick(FONT_WEIGHTS),
    cardRadius: rng.pick(CARD_RADII),
    cardPadding: rng.int(32, 48),
    transitions: rng.pickN(TRANSITION_POOL, rng.int(2, 3)),
    springDamping: rng.range(10, 15),
    staggerDelay: rng.range(0.1, 0.2),
  };
}

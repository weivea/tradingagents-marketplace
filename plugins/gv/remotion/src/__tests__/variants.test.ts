import { describe, it, expect } from "vitest";
import { generateVariant } from "../theme/variants";

describe("generateVariant", () => {
  it("produces deterministic variant for same seed", () => {
    const a = generateVariant("MSFT_2026-04-10");
    const b = generateVariant("MSFT_2026-04-10");
    expect(a).toEqual(b);
  });

  it("produces different variant for different seed", () => {
    const a = generateVariant("MSFT_2026-04-10");
    const b = generateVariant("NIO_2026-04-10");
    const differs = a.hueShift !== b.hueShift || a.gradientAngle !== b.gradientAngle;
    expect(differs).toBe(true);
  });

  it("hueShift is within ±30", () => {
    const v = generateVariant("test");
    expect(v.hueShift).toBeGreaterThanOrEqual(-30);
    expect(v.hueShift).toBeLessThanOrEqual(30);
  });

  it("generates 3-5 orbs", () => {
    const v = generateVariant("test");
    expect(v.orbs.length).toBeGreaterThanOrEqual(3);
    expect(v.orbs.length).toBeLessThanOrEqual(5);
  });

  it("picks 2-3 transitions", () => {
    const v = generateVariant("test");
    expect(v.transitions.length).toBeGreaterThanOrEqual(2);
    expect(v.transitions.length).toBeLessThanOrEqual(3);
  });
});

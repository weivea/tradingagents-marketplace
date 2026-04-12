import { describe, it, expect } from "vitest";
import { SeededRandom } from "../utils/seeded-random";

describe("SeededRandom", () => {
  it("produces deterministic output for same seed", () => {
    const a = new SeededRandom("MSFT_2026-04-10");
    const b = new SeededRandom("MSFT_2026-04-10");
    expect(a.next()).toBe(b.next());
    expect(a.next()).toBe(b.next());
  });

  it("produces different output for different seeds", () => {
    const a = new SeededRandom("MSFT_2026-04-10");
    const b = new SeededRandom("NIO_2026-04-10");
    const aVals = Array.from({ length: 5 }, () => a.next());
    const bVals = Array.from({ length: 5 }, () => b.next());
    expect(aVals).not.toEqual(bVals);
  });

  it("range() returns value within bounds", () => {
    const rng = new SeededRandom("test");
    for (let i = 0; i < 100; i++) {
      const v = rng.range(10, 20);
      expect(v).toBeGreaterThanOrEqual(10);
      expect(v).toBeLessThanOrEqual(20);
    }
  });

  it("pick() returns element from array", () => {
    const rng = new SeededRandom("test");
    const items = ["a", "b", "c"];
    for (let i = 0; i < 20; i++) {
      expect(items).toContain(rng.pick(items));
    }
  });

  it("pickN() returns N unique elements", () => {
    const rng = new SeededRandom("test");
    const items = ["a", "b", "c", "d", "e"];
    const picked = rng.pickN(items, 3);
    expect(picked).toHaveLength(3);
    expect(new Set(picked).size).toBe(3);
  });
});

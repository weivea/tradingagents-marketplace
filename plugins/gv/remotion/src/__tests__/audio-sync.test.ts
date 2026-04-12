import { describe, it, expect } from "vitest";
import { calcSectionTimings } from "../utils/audio-sync";

describe("calcSectionTimings", () => {
  it("allocates frames proportional to tts_text length", () => {
    const sections = [
      { type: "title" as const, headline: "", body: "", tts_text: "你好世界你好世界" },
      { type: "point" as const, headline: "", body: "", tts_text: "你好" },
    ];
    const timings = calcSectionTimings(sections, 10, 30);
    expect(timings).toHaveLength(2);
    expect(timings[0].durationFrames).toBeGreaterThan(timings[1].durationFrames);
    expect(timings[0].durationFrames + timings[1].durationFrames).toBe(300);
  });

  it("enforces minimum 2 seconds per section", () => {
    const sections = [
      { type: "title" as const, headline: "", body: "", tts_text: "你" },
      { type: "point" as const, headline: "", body: "", tts_text: "你好世界你好世界你好世界你好世界你好世界你好" },
    ];
    const timings = calcSectionTimings(sections, 10, 30);
    expect(timings[0].durationFrames).toBeGreaterThanOrEqual(60);
  });

  it("startFrame values are sequential", () => {
    const sections = [
      { type: "title" as const, headline: "", body: "", tts_text: "你好" },
      { type: "point" as const, headline: "", body: "", tts_text: "你好" },
      { type: "conclusion" as const, headline: "", body: "", tts_text: "你好" },
    ];
    const timings = calcSectionTimings(sections, 9, 30);
    expect(timings[0].startFrame).toBe(0);
    expect(timings[1].startFrame).toBe(timings[0].durationFrames);
    expect(timings[2].startFrame).toBe(timings[0].durationFrames + timings[1].durationFrames);
  });
});

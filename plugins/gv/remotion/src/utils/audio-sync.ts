import type { Section, SectionTiming } from "../types";

export function calcSectionTimings(
  sections: Pick<Section, "type" | "tts_text">[],
  totalDuration: number,
  fps: number,
): SectionTiming[] {
  const totalFrames = Math.ceil(totalDuration * fps);
  const n = sections.length;
  if (n === 0) return [];

  const minFrames = 2 * fps;
  const charCounts = sections.map((s) => s.tts_text.length || 1);
  const totalChars = charCounts.reduce((a, b) => a + b, 0);

  let durations = charCounts.map((c) => Math.round((c / totalChars) * totalFrames));

  for (let i = 0; i < durations.length; i++) {
    if (durations[i] < minFrames) {
      durations[i] = minFrames;
    }
  }

  // Redistribute excess/deficit only among non-minimum sections
  const sum = durations.reduce((a, b) => a + b, 0);
  if (sum !== totalFrames) {
    const diff = totalFrames - sum;
    const flexIndices = durations
      .map((d, i) => (d > minFrames ? i : -1))
      .filter((i) => i >= 0);

    if (flexIndices.length > 0) {
      const flexSum = flexIndices.reduce((a, i) => a + durations[i], 0);
      let distributed = 0;
      for (let j = 0; j < flexIndices.length; j++) {
        const i = flexIndices[j];
        const share = Math.round((durations[i] / flexSum) * diff);
        durations[i] += share;
        distributed += share;
      }
      // Fix any rounding remainder on the last flex section
      durations[flexIndices[flexIndices.length - 1]] += diff - distributed;
    } else {
      // All sections are at minimum — adjust last section
      durations[durations.length - 1] += diff;
    }
  }

  const timings: SectionTiming[] = [];
  let startFrame = 0;
  for (let i = 0; i < n; i++) {
    timings.push({
      type: sections[i].type,
      startFrame,
      durationFrames: durations[i],
    });
    startFrame += durations[i];
  }

  return timings;
}

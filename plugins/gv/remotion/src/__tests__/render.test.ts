import { describe, it, expect } from "vitest";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import fs from "fs";

describe("ShortVideo render", () => {
  it("renders a 3-second test video", async () => {
    const entryPoint = path.resolve(__dirname, "../index.ts");
    const bundled = await bundle(entryPoint);

    const testProps = {
      sections: [
        { type: "title", headline: "测试标题", body: "2026-04-12", tts_text: "测试标题" },
        { type: "rating", headline: "买入", body: "目标价 $100", highlights: ["+20%"], tts_text: "买入", metrics: [] },
        { type: "conclusion", headline: "结论", body: "建议买入", highlights: [], tts_text: "结论" },
      ],
      timestamps: [],
      audioPath: "",
      totalDuration: 10,
      seed: "TEST_2026-04-12",
    };

    const composition = await selectComposition({
      serveUrl: bundled,
      id: "ShortVideo",
      inputProps: testProps,
    });

    const outputPath = path.resolve(__dirname, "../../test-output.mp4");

    await renderMedia({
      composition,
      serveUrl: bundled,
      codec: "h264",
      outputLocation: outputPath,
    });

    expect(fs.existsSync(outputPath)).toBe(true);
    const stat = fs.statSync(outputPath);
    expect(stat.size).toBeGreaterThan(1000);

    // Cleanup
    fs.unlinkSync(outputPath);
  }, 120_000);
});

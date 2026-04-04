import { callPython } from "./call-python.js";

export interface RenderFramesParams {
  sections_path: string;
  layout: "full" | "short";
  output_dir: string;
}

export async function renderFrames(params: RenderFramesParams): Promise<string> {
  const { sections_path, layout, output_dir } = params;
  try {
    return await callPython([
      "render",
      "--sections", sections_path,
      "--layout", layout,
      "--output-dir", output_dir,
    ]);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}

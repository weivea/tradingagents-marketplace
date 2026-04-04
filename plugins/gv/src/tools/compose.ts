import { callPython } from "./call-python.js";

export interface ComposeVideoParams {
  frames_dir: string;
  audio_path: string;
  timestamps_path: string;
  layout: "full" | "short";
  output_path: string;
}

export async function composeVideo(params: ComposeVideoParams): Promise<string> {
  const { frames_dir, audio_path, timestamps_path, layout, output_path } = params;
  try {
    return await callPython([
      "compose",
      "--frames-dir", frames_dir,
      "--audio", audio_path,
      "--timestamps", timestamps_path,
      "--layout", layout,
      "--output", output_path,
    ]);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}

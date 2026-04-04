import { callPython } from "./call-python.js";

export interface GenerateTtsParams {
  text: string;
  output_dir: string;
  voice?: string;
  rate?: string;
}

export async function generateTts(params: GenerateTtsParams): Promise<string> {
  const { text, output_dir, voice, rate } = params;
  const args = ["tts", "--text", text, "--output-dir", output_dir];
  if (voice) args.push("--voice", voice);
  if (rate) args.push("--rate", rate);
  try {
    return await callPython(args);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}

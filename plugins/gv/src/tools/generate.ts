import { callPython } from "./call-python.js";

export interface GenerateVideoParams {
  report_path: string;
  version?: "full" | "short" | "both";
}

export async function generateVideo(params: GenerateVideoParams): Promise<string> {
  const { report_path, version } = params;
  const args = ["generate", report_path];
  if (version) args.push("--version", version);
  try {
    return await callPython(args);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}

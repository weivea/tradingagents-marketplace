import { callPython } from "./call-python.js";

export interface ParseReportParams {
  report_path: string;
}

export async function parseReport(params: ParseReportParams): Promise<string> {
  const { report_path } = params;
  try {
    return await callPython(["parse", report_path]);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}

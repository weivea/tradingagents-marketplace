import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.resolve(__dirname, "../..");

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "uv",
      ["run", "--project", PLUGIN_DIR, "python", "-m", "python", ...args],
      {
        cwd: PLUGIN_DIR,
        timeout: 60_000,
        maxBuffer: 10 * 1024 * 1024,
        encoding: "utf-8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
      (err, stdout, stderr) => {
        if (err) reject(new Error(`Python error: ${stderr || err.message}`));
        else resolve(stdout);
      }
    );
  });
}

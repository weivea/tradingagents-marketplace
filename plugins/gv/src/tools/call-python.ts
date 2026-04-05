import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.resolve(__dirname, "../..");  // plugins/gv/

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "uv",
      ["run", "--project", PLUGIN_DIR, "python", "-m", "python", ...args],
      {
        cwd: PLUGIN_DIR,
        timeout: 3_600_000,  // 60 min – full-layout video encoding needs more than 10 min
        maxBuffer: 50 * 1024 * 1024,  // 50MB for large JSON output
        encoding: "utf-8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
      (err, stdout, stderr) => {
        if (err) {
          reject(new Error(`Python error: ${stderr || err.message}`));
        } else {
          resolve(stdout);
        }
      }
    );
  });
}

import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PYTHON_DIR = path.resolve(__dirname, "../../python");

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "python",
      ["-m", "python", ...args],
      {
        cwd: PYTHON_DIR.replace(/[/\\]python$/, ""),  // run from plugins/gv/
        timeout: 600_000,
        maxBuffer: 50 * 1024 * 1024,  // 50MB for large JSON output
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

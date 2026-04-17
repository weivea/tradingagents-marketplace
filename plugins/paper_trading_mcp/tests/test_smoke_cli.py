"""End-to-end smoke test: exercise CLI subcommands against a real temp SQLite DB."""
import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(args, env):
    result = subprocess.run(
        [sys.executable, "-m", "python", *args],
        cwd=Path(__file__).resolve().parent.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


def test_cli_end_to_end(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    res = run_cli([
        "place-order", "--account-id", "aggressive", "--symbol", "AAPL",
        "--market", "US", "--side", "buy", "--qty", "10",
        "--order-type", "market", "--ref-price", "150.0",
    ], env)
    assert res["ok"] is True
    assert res["status"] == "filled"

    pf = run_cli([
        "get-portfolio", "--account-id", "aggressive",
        "--price-map", json.dumps({"AAPL": 160.0}),
    ], env)
    assert len(pf["positions"]) == 1
    assert pf["positions"][0]["symbol"] == "AAPL"
    assert pf["positions"][0]["market_value"] == 1600.0

    run_cli([
        "append-journal", "--account-id", "aggressive", "--date", "2026-04-17",
        "--markdown", "Bought AAPL @ 150.",
    ], env)
    j = run_cli([
        "read-journal", "--account-id", "aggressive", "--date", "2026-04-17",
    ], env)
    assert "Bought AAPL" in j["content"]

    run_cli([
        "init-discussion", "--date", "2026-04-17",
        "--pnl-summary", json.dumps({"aggressive": 2.3, "neutral": 0.5, "conservative": -0.1}),
    ], env)
    run_cli([
        "append-discussion", "--date", "2026-04-17", "--speaker", "aggressive",
        "--markdown", "Crushed it.", "--next-speaker", "conservative",
        "--reason", "provoke",
    ], env)
    d = run_cli(["read-discussion", "--date", "2026-04-17"], env)
    assert "Crushed it" in d["content"]
    assert "next_speaker: conservative" in d["content"]

    assert (tmp_path / ".paper_trading" / "paper.db").exists()
    assert (tmp_path / ".paper_trading" / "journals" / "aggressive-2026-04-17.md").exists()
    assert (tmp_path / ".paper_trading" / "discussions" / "2026-04-17.md").exists()

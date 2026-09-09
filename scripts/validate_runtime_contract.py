from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    tracked = tracked_files()

    # 1) Secret files themselves must never be tracked.
    forbidden_secret_files = {
        p
        for p in tracked
        if p == "providers.env" or (p.endswith(".env") and not p.endswith(".env.example"))
    }
    if forbidden_secret_files:
        fail(errors, f"tracked secret env files: {sorted(forbidden_secret_files)}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in ("providers.env", "*.env"):
        if required not in gitignore:
            fail(errors, f".gitignore must protect {required}")

    # 2) Provider contract: Gemini + OpenRouter only; GitHub auth is not required to run.
    provider_example = (ROOT / "providers.env.example").read_text(encoding="utf-8")
    for required in ("GEMINI_API_KEY_1=", "OPENROUTER_API_KEY_1="):
        if required not in provider_example:
            fail(errors, f"providers.env.example missing {required}")
    for forbidden in (
        "GROQ_API_KEY",
        "DEEPSEEK_API_KEY",
        "NVIDIA_API_KEY",
        "GITHUB_TOKEN",
        "GITHUB_API_KEY",
    ):
        if forbidden in provider_example:
            fail(errors, f"providers.env.example unexpectedly requires {forbidden}")

    # 3) Best-effort committed-secret signature scan over text-like tracked files.
    text_suffixes = {".py", ".md", ".yaml", ".yml", ".json", ".jsonl", ".ipynb", ".txt", ".example"}
    secret_patterns = {
        "Gemini-like API key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
        "OpenRouter-like API key": re.compile(r"sk-or-v1-[0-9A-Za-z_-]{20,}"),
    }
    for rel in tracked:
        path = ROOT / rel
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in secret_patterns.items():
            if pattern.search(text):
                fail(errors, f"{rel}: possible committed {label}")

    # 4) Colab must satisfy the promised one-cell quick-resume contract.
    notebook_path = ROOT / "notebooks" / "VietRAG_Colab.ipynb"
    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(errors, f"Colab notebook is not valid JSON: {type(exc).__name__}")
        notebook = {}

    if int(notebook.get("nbformat", 0)) < 4:
        fail(errors, "Colab notebook must use nbformat >= 4")

    code_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if not code_cells:
        fail(errors, "Colab notebook has no code cells")
    else:
        all_code = "\n".join(code_cells)
        if "scripts/build_index.py" not in all_code:
            fail(errors, "FULL UPDATE / BUILD cell does not build the persistent index")
        if "scripts/validate_sources.py" not in all_code:
            fail(errors, "FULL UPDATE / BUILD cell does not validate source provenance")

        quick = code_cells[-1]
        required_quick_fragments = (
            "/content/providers.env",
            "/content/drive/MyDrive/CAND_VB2_RAG/index",
            "drive.mount",
            "faiss.index",
            "chunks.jsonl",
            "index_manifest.json",
            "VIETRAG_INDEX_DIR",
            "SRC_DIR = REPO_DIR / 'src'",
            "sys.path.insert(0, src_path)",
            "find_spec('vietrag')",
            "import app",
            "demo.launch",
        )
        for fragment in required_quick_fragments:
            if fragment not in quick:
                fail(errors, f"final quick-resume cell missing {fragment}")
        if "scripts/build_index.py" in quick or "embed_documents" in quick:
            fail(errors, "final quick-resume cell must never rebuild/re-embed the corpus")
        if "GITHUB_TOKEN" in quick or "GITHUB_API_KEY" in quick:
            fail(errors, "final quick-resume cell must not require GitHub credentials")
        if "subprocess.run([sys.executable, 'app.py']" in quick:
            fail(errors, "final quick-resume cell must launch Gradio in-kernel, not through a blocking subprocess")

    # 5) Runtime code must honor the persistent Drive index and private env overrides.
    config_text = (ROOT / "src" / "vietrag" / "config.py").read_text(encoding="utf-8")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    if "VIETRAG_INDEX_DIR" not in config_text:
        fail(errors, "config.py does not honor VIETRAG_INDEX_DIR")
    if "VIETRAG_ENV" not in app_text:
        fail(errors, "app.py does not honor VIETRAG_ENV")

    # 6) CI smoke-test the src-layout exactly the way Colab quick-resume imports it.
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.path.insert(0, 'src'); "
                "import vietrag; "
                "from vietrag.config import load_config; "
                "print(vietrag.__file__)"
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if smoke.returncode != 0:
        fail(errors, "src-layout import smoke test failed: " + (smoke.stderr.strip() or smoke.stdout.strip()))

    for error in errors:
        print("ERROR:", error)
    if errors:
        print(f"Runtime contract validation: FAIL ({len(errors)} issue(s))")
        return 1

    print("Runtime contract validation: PASS")
    print("- secrets are not tracked")
    print("- Gemini + OpenRouter only")
    print("- quick resume loads the persistent Drive index without rebuilding")
    print("- quick resume injects repo/src into the running Colab kernel before import")
    print("- no GitHub API key/token is required for normal Colab use")
    return 0


if __name__ == "__main__":
    sys.exit(main())

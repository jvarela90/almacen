# ai_agent/ai_devops.py
#!/usr/bin/env python3
import logging
import argparse
import datetime
from pathlib import Path
import git
import json
from typing import Dict

from .config import (
    ROOT, GIT_REMOTE, GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL,
    DEV_NOTES, REVIEW_REPORT, AI_RESPONSE_FILE, AI_SUGGESTED_DIR,
    AUTO_PUSH_DEFAULT, DRY_RUN_DEFAULT
)
from .ai_helpers import (
    run_cmd, safe_load_json, safe_write_json,
    call_openai_chat, call_claude, extract_json_from_text
)

# === logging ===
LOGFILE = str(Path(ROOT / "ai_logs" / f"session_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.log"))
logging.basicConfig(level=logging.INFO, filename=LOGFILE,
                    format="%(asctime)s %(levelname)s %(message)s")
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)
logger = logging.getLogger("ai_devops")

# === helpers ===
def git_repo() -> git.Repo:
    return git.Repo(str(ROOT))

def collect_repo_summary(limit_files=200) -> Dict:
    repo = git_repo()
    changed = [str(p) for p in repo.untracked_files] + [str(item.a_path) for item in repo.index.diff(None)]
    status = {
        "head": repo.head.commit.hexsha if repo.head.is_valid() else None,
        "branch": repo.active_branch.name,
        "dirty": repo.is_dirty(),
        "untracked_or_modified": changed[:limit_files],
    }
    files = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix not in (".pyc", ".db", ".sqlite", ".sqlite3"):
            files.append(str(p.relative_to(ROOT)))
            if len(files) >= limit_files:
                break
    status["files_sample"] = files
    return status

def run_checks() -> Dict:
    results = {}
    rc, out = run_cmd("pytest -q", cwd=ROOT)
    results["pytest_rc"] = rc
    results["pytest_out"] = out
    rc, out = run_cmd("black --check .", cwd=ROOT)
    results["black_rc"] = rc
    results["black_out"] = out
    rc, out = run_cmd("flake8 . || true", cwd=ROOT)
    results["flake8_out"] = out
    return results

def create_branch(base_branch: str = None) -> str:
    repo = git_repo()
    base = base_branch or repo.active_branch.name
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    branch = f"ai/auto-{ts}"
    logger.info("Creating branch %s from %s", branch, base)
    repo.git.checkout(base)
    repo.git.pull(GIT_REMOTE, base)
    repo.git.checkout(b=branch)
    return branch

def apply_ai_files(files_map: Dict[str, str], commit_message: str, author_name: str):
    repo = git_repo()
    for rel, content in files_map.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        logger.info("Wrote %s", rel)
    repo.git.add(A=True)
    actor = git.Actor(author_name, GIT_AUTHOR_EMAIL)
    repo.index.commit(commit_message, author=actor)
    logger.info("Committed changes with message: %s", commit_message)

def save_ai_response(text: str):
    AI_RESPONSE_FILE.write_text(text, encoding="utf-8")
    logger.info("AI response saved to %s", AI_RESPONSE_FILE)

# === main flow ===
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", help="base branch", default=None)
    parser.add_argument("--use-claude", action="store_true", help="use Claude for implementer role")
    parser.add_argument("--auto-apply", action="store_true", help="apply AI returned changes (if JSON present)")
    parser.add_argument("--auto-push", action="store_true", help="push branch to remote after commit")
    parser.add_argument("--dry-run", action="store_true", help="do not change files (override .env)")
    args = parser.parse_args()

    dry_run = args.dry_run or DRY_RUN_DEFAULT
    auto_push = args.auto_push or AUTO_PUSH_DEFAULT

    repo_summary = collect_repo_summary()
    checks = run_checks()

    logger.info("Repo summary: %s", repo_summary)
    logger.info("Checks summary: pytest rc %s", checks.get("pytest_rc"))

    # build prompt for implementer IA (Claude) to apply changes locally
    implementer_goal = (
        "Eres el IMPLEMENTADOR (Claude Code local). Lee el repo y las notas previas (si las hay). "
        "Aplica cambios concretos que mejoren estructura: migraciones .ui, reorganización MVC, "
        "limpieza y fusion de esquemas SQL. Devuelve un JSON con keys: files (path->content) y commit_message. "
        "Si no realizarás cambios, devuelve JSON vacío: {\"files\":{}, \"commit_message\":\"\"}."
    )

    prompt_impl = f"Repo summary:\n{json.dumps(repo_summary, indent=2)}\nChecks:\n{json.dumps(checks, indent=2)}\nGoal:\n{implementer_goal}\n\nDev notes file path: ai_sync/dev_notes.json"

    # Call implementer IA
    impl_response = ""
    try:
        if args.use_claude:
            impl_response = call_claude(prompt_impl)
        else:
            impl_response = call_openai_chat(prompt_impl, system="You are a senior developer/implementer.", temperature=0.0)
    except Exception as e:
        logger.error("Implementer AI failed: %s", e)
        return

    save_ai_response(impl_response)
    parsed = extract_json_from_text(impl_response)
    if not parsed:
        logger.warning("No structured JSON returned by implementer. See ai_response.md")
        # save suggestion and exit
        (AI_SUGGESTED_DIR / "raw_impl_response.md").write_text(impl_response, encoding="utf-8")
        return

    files_map = parsed.get("files", {})
    commit_msg = parsed.get("commit_message", "AI: implementer changes")

    # Save dev_notes for reviewer to read
    dev_notes = {"implementer_summary": parsed.get("summary", ""), "files_changed": list(files_map.keys())}
    safe_write_json(DEV_NOTES, dev_notes)

    # Optionally apply
    if files_map and args.auto_apply and not dry_run:
        branch = create_branch(args.branch)
        apply_ai_files(files_map, commit_msg, author_name="Claude (implementer)")
        # run post checks
        post_checks = run_checks()
        safe_write_json(Path("ai_post_checks.json"), post_checks)
        logger.info("Post-checks written")
        if auto_push:
            repo = git_repo()
            repo.git.push("--set-upstream", GIT_REMOTE, branch)
            logger.info("Pushed branch %s", branch)
    else:
        # write suggested files for manual review
        for rel, content in files_map.items():
            target = AI_SUGGESTED_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        logger.info("Saved suggested files to %s for manual review", AI_SUGGESTED_DIR)

    # Now reviewer (ChatGPT) reads dev_notes and repo, returns review_report.json
    reviewer_goal = (
        "Eres el REVISOR (ChatGPT). Lee ai_sync/dev_notes.json y el repo. Produce JSON with:"
        " findings (list), approved_changes (list of filepaths), requested_changes (list of dicts)."
    )
    review_prompt = f"Repo summary:\n{json.dumps(repo_summary, indent=2)}\nDev notes:\n{json.dumps(dev_notes, indent=2)}\nGoal:\n{reviewer_goal}"
    try:
        review_text = call_openai_chat(review_prompt, system="You are a senior code reviewer.", temperature=0.0)
    except Exception as e:
        logger.error("Reviewer AI failed: %s", e)
        return

    # Save review
    safe_write_json(REVIEW_REPORT, {"raw": review_text})
    parsed_review = extract_json_from_text(review_text)
    if parsed_review:
        safe_write_json(REVIEW_REPORT, parsed_review)
        logger.info("Review report saved to %s", REVIEW_REPORT)
    else:
        (AI_SUGGESTED_DIR / "raw_review.txt").write_text(review_text, encoding="utf-8")
        logger.warning("Reviewer did not return structured JSON; saved raw review")

    logger.info("AI cycle complete. Review %s for results.", REVIEW_REPORT)

if __name__ == "__main__":
    main()

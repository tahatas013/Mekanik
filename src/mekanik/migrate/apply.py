# SPDX-License-Identifier: AGPL-3.0-or-later
"""The real migration, `mekanik migrate surec-work --apply` (architecture §14.1–14.3). The dry run and V1–V8 come
first; only when every V passes do the files go to a new branch <code>/work/v1-migration of the organization repo,
in the work's worktree (<works_root>/work/<code>), with the migration-gap card MG-01 (hold) open, in one team commit.
Old branches are not touched: the new branch starts from the repo's current branch, and <code>/main (v1's gate
branch) is made there when missing. The chief's signed approval of MG-01 then covers the migrated approvals and the
gates passed in surec (APPROVAL-02)."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from mekanik.core import yamlio
from mekanik.core.i18n import t
from mekanik.core.process import refuse
from mekanik.core.store import git, works

from .convert import GAP_CARD, surec_work
from .verify import verify


def apply(old_work, config, old: dict | None, known=None) -> dict:
    """→ {code, branch, path, commit, report}. Refused (migrate.apply.*) without the old-side snapshot, when a V does
    not pass, or when the branch or the worktree is there already."""
    refuse(not old, "migrate.apply.no_snapshot")
    with tempfile.TemporaryDirectory(prefix="mekanik-apply-") as tmp:
        code = surec_work(old_work, tmp, config, old=old).code
        org, branch, main = config.org(code[:3]), f"{code}/work/v1-migration", f"{code}/main"
        yamlio.write(Path(tmp) / "work.yaml", yamlio.read(Path(tmp) / "work.yaml") | {
            "branches": {"main": main, "work": [branch]}})
        res = verify(old_work, tmp, config, old=old, known=known)
        bad = [f"{v}: {r['status']} ({'; '.join(map(str, r['details']))[:200]})" for v, r in res.items()
               if r["status"] != "pass"]
        refuse(bad, "migrate.apply.verify", items=" · ".join(bad))
        repo, tree = Path(os.path.expanduser(org["repo"])), config.path("works_root") / "work" / code
        refuse(git.branch_exists(repo, branch) or tree.exists(), "migrate.apply.exists", branch=branch, path=str(tree))
        works.setup_repo(repo)
        base = git.git("symbolic-ref", "--short", "HEAD", cwd=repo)
        if not git.branch_exists(repo, main):
            git.git("branch", main, base, cwd=repo)
        git.git("worktree", "add", "-q", "-b", branch, str(tree), base, cwd=repo)
        p = next(x for x in org.get("projects") or [] if x["code"] == code[4:7])
        dest = tree / p.get("folder", p["code"].lower()) / code
        git.git("rm", "-r", "-q", "--ignore-unmatch", "--", str(dest), cwd=tree)   # an old folder at that place
        shutil.copytree(tmp, dest, dirs_exist_ok=True)
    sha = git.commit(tree, git.message(t("migrate.apply.title", code=code), t("migrate.apply.step", code=code, n=len(
        yamlio.read(dest / "records" / "migration.yaml")["gaps"])), "project_engineer", [GAP_CARD]), [str(dest)],
        config.team)
    return {"code": code, "branch": branch, "path": dest, "commit": sha, "report": res}

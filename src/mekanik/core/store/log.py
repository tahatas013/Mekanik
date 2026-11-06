# SPDX-License-Identifier: AGPL-3.0-or-later
"""Work log (old `gunluk.py`, handbook §11): records/log/YYYY-MM-DD.md, append-only, the time from the system clock;
an entry is time · role (not the model) · kind, title, text, visuals, check summary, cards and version."""

import os
from datetime import datetime
from pathlib import Path

from .. import clock
from ..i18n import t

FOLDER = "records/log"
MAX_VISUALS = 3   # source: assumption — old gunluk.EN_COK_GORSEL (handbook §14 open item, default kept)


def write(root, code: str, role: str, kind: str, title: str, text: str = "", visuals=(), summary: dict | None = None,
          cards=(), commit: str | None = None, branch: str | None = None) -> Path:
    at = datetime.fromisoformat(clock.now())
    path = Path(root) / FOLDER / f"{at:%Y-%m-%d}.md"
    lines = [] if path.exists() else [t("store.log.head", code=code, date=f"{at:%Y-%m-%d}"), ""]
    lines += [f"### {at:%H:%M} · {t('store.log.role.' + role)} · {t('store.log.kind.' + kind)}", "", f"**{title}**", ""]
    lines += [text.strip(), ""] if text.strip() else []
    for v in list(visuals)[:MAX_VISUALS]:
        lines += [f"![{Path(v).stem}]({os.path.relpath(v, FOLDER)})", ""]
    lines += [t("store.log.checks", **summary)] if summary is not None else []
    lines += [t("store.log.cards", ids=", ".join(cards))] if cards else []
    lines += [t("store.log.version", commit=(commit or "")[:7], branch=branch or "")] if commit else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines + [""]) + "\n")
    return path


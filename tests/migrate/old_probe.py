# SPDX-License-Identifier: AGPL-3.0-or-later
"""Old-side snapshot for V4–V7. Runs inside the OLD `surec` environment (imports only `surec_cekirdek`):

    python -P -B tests/migrate/old_probe.py <old work> <surec data root: profiller/ + kurumlar/>  > snapshot.json

The work is copied to a temp folder first; nothing is written next to it or into the old repo."""

import json
import shutil
import sys
import tempfile
from pathlib import Path


def main(work: str, data: str) -> dict:
    from surec_cekirdek import kartlar, kontroller, modelci, onay, veri

    root = Path(tempfile.mkdtemp())
    shutil.copytree(Path(data) / "profiller", root / "profiller")
    for f in (Path(data) / "kurumlar").glob("*"):   # kurumlar/<kod>/kurum.yaml or kurumlar/<KOD>.yaml
        src = f / "kurum.yaml" if f.is_dir() else f
        (root / "kurumlar" / f.stem.lower()).mkdir(parents=True, exist_ok=True)
        shutil.copy(src, root / "kurumlar" / f.stem.lower() / "kurum.yaml")
    veri.SUREC_KOK = onay.SUREC_KOK = root
    shutil.copytree(work, root / "work")
    c = veri.calisma_yukle(root / "work")
    model = modelci.uret(c)
    res = kontroller.calistir(c, model)
    cards = kartlar.uret(c, res)
    bb = {a: s.BoundingBox() for a, s in (model or {}).items()}   # same quantities as mech ModelHooks.metrics
    return {"code": c.kod, "stage": c.asama,
            "results": [{"check": s.kontrol, "rule": s.kural, "status": s.durum, "ref": s.ref, "value": s.deger,
                         "param": s.ek.get("param")} for s in res],
            "cards": [{"id": k["no"], "key": k.get("anahtar"), "status": k.get("durum"),
                       "triggers": k.get("tetikleyiciler"),
                       "subject_hash": onay.ozet(onay.konu_degerleri(c, k.get("konu") or {}))} for k in cards],
            "model": {a: {"volume": s.Volume(), "faces": len(s.Faces()), "solids": len(s.Solids()),
                          "bbox": [bb[a].xlen, bb[a].ylen, bb[a].zlen]} for a, s in (model or {}).items()}}


if __name__ == "__main__":
    json.dump(main(sys.argv[1], sys.argv[2]), sys.stdout, ensure_ascii=False, indent=1, default=str)

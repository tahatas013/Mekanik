# SPDX-License-Identifier: AGPL-3.0-or-later
"""The panel's FastAPI shell (old uygulama.py): REST reads and writes under /api, live events over SSE, the PTY
WebSocket of the session tab (A13; its terminal comes in wave 2.3), the built front end. The API contract is
docs/dev/panel-api.md. Errors are {"error": {"key", "text", "data"}}: the key is the catalog key, tests read it."""

from __future__ import annotations

import asyncio
import io
import json
import os
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Query, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel

from mekanik.config import load_config
from mekanik.core import data, i18n
from mekanik.core.errors import GitError, MekanikError
from mekanik.core.i18n import t
from mekanik.core.process import Refused

from . import auth, events, model, reads, writes

KEEPALIVE = 15   # source: assumption — old olaylar: seconds between two keep-alive comments of the event stream
SANDBOX = {"Content-Security-Policy": "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; sandbox",
           "X-Content-Type-Options": "nosniff"}   # a served SVG or file runs no script, even opened on its own
WS_DENIED, WS_LATER = 4401, 4501   # WebSocket close codes: no session; the terminal is wave 2.3 (A13)


def dist() -> Path:
    """The built front end: in the wheel (panel/static) or the checkout's panel-ui/dist (wave 2.3)."""
    own = Path(__file__).with_name("static")
    return own if own.is_dir() else data.REPO_ROOT / "panel-ui" / "dist"


def _error(status: int, key: str, **kw) -> JSONResponse:
    safe = json.loads(json.dumps(kw, ensure_ascii=False, default=str))
    return JSONResponse({"error": {"key": key, "text": t(key, **kw) if i18n.has(key) else key, "data": safe}},
                        status_code=status)


def create_app(watch: bool = True) -> FastAPI:
    """The panel application; `watch` starts the event watcher with it (tests of plain reads leave it off)."""
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"   # E-20: the panel's git reads never take the index lock
    watcher = events.Watcher()

    @asynccontextmanager
    async def life(_app):
        watch and watcher.start()
        yield
        watcher.stopped.set()

    app = FastAPI(title="mekanik panel", lifespan=life, docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    app.state.watcher = watcher

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if no := auth.refusal(request.method, request.url.path, request.client and request.client.host,
                              request.headers):
            return _error(*no)
        return await call_next(request)

    for exc, status in ((Refused, 409), (MekanikError, 409), (GitError, 409), (PermissionError, 403),
                        (reads.Unknown, 404)):
        app.add_exception_handler(exc, lambda _r, e, s=status: _error(s, getattr(e, "key", "panel.error"), **{
            **getattr(e, "data", {}), **({} if hasattr(e, "key") else {"error": str(e)})}))
    _routes(app)
    return app


class Decision(BaseModel):
    action: Literal["approve", "reject", "comment"]
    reason: str = ""
    option: str | None = None
    rows: list[str] | None = None
    viewed: str | None = None
    branch: str | None = None
    confirmed: bool = False


class Undo(BaseModel):
    reason: str = ""
    row: str | None = None
    viewed: str | None = None
    branch: str | None = None
    confirmed: bool = False


class Value(BaseModel):
    param: str
    value: float
    reason: str = ""
    card: str | None = None
    viewed: str | None = None
    branch: str | None = None


class Note(BaseModel):
    text: str
    png: str
    commit: str | None = None
    part: str | None = None
    point: list[float] | None = None
    camera: dict | None = None
    box: list[float] | None = None


class Reason(BaseModel):
    reason: str = ""
    viewed: str | None = None
    confirmed: bool = False


class NewWork(BaseModel):
    org: str
    project: str
    title: str
    risk_class: str
    purpose: str = ""
    done_criterion: str = ""
    work_type: str | None = None


class Measure(BaseModel):
    work: str
    commit: str
    tool: str = "PropertiesMeasurement"
    paths: list[str]
    center: bool = False


class Branch(BaseModel):
    commit: str
    name: str


class Text(BaseModel):
    text: str = ""


class Answer(BaseModel):
    key: str
    value: Any


def _routes(app: FastAPI) -> None:   # noqa: C901 — one table of thin handlers
    get, post = app.get, app.post
    W = "/api/works/{code}"

    @get("/login")
    def login(token: str = "", next: str = "/"):
        if not auth.same(token, auth.secret()):
            return _error(401, "panel.auth.session")
        safe = next.startswith("/") and not next.startswith("//") and "\\" not in next   # no open redirect
        r = RedirectResponse(next if safe else "/", status_code=303)
        r.set_cookie(auth.COOKIE, auth.session_value(), httponly=True, samesite="strict", path="/")
        return r

    @get("/api/session")
    def session():
        cfg = load_config()
        return {"csrf": auth.csrf_token(), "chief": cfg.chief[0], "signing_key": cfg.signing_key, "lang": i18n.lang(),
                "upload_limit": writes.upload_limit()}

    @get("/api/catalog")
    def catalog(lang: str = ""):
        cats = i18n.catalogs()
        base, own = cats.get("tr", {}), cats.get(lang or i18n.lang(), {})
        keep = ("panel.", "status.", "agent.liveness.", "num.")
        return {k: own.get(k) or v for k, v in base.items() if k.startswith(keep) and not k.startswith("panel.mcp.")}

    get("/api/tree")(reads.tree)
    get("/api/tabs")(reads.tabs)
    get("/api/cards")(reads.all_cards)
    get("/api/new-work")(reads.new_work_options)
    get(W)(reads.work)
    get(W + "/stages")(reads.stages)
    get(W + "/status")(reads.status)
    get(W + "/liveness")(reads.liveness)
    get(W + "/cards")(reads.cards)
    get(W + "/calcs")(reads.calcs)
    get(W + "/files")(reads.files)
    get(W + "/branches")(reads.branches)
    get(W + "/design-file")(reads.design_file)
    get(W + "/summary")(reads.day_summary)
    get(W + "/intake")(reads.intake)
    get(W + "/stdmap")(reads.stdmap)
    get(W + "/policy")(reads.policy)
    get(W + "/steps/{sha}")(reads.step_detail)

    @get(W + "/stream")
    def stream_(code: str, offset: int = 0):
        from mekanik.core.report import stream

        got, end = stream.since(reads.root_of(code), offset)
        return {"code": code, "events": got, "offset": end}

    @get(W + "/inbox")
    def inbox_(code: str):
        from mekanik.agent import inbox

        reads.root_of(code)
        return {"code": code, "items": inbox.items(code)}

    @get(W + "/download/{path:path}")
    def download(code: str, path: str):
        target = reads.download(code, path)
        if target.is_file():
            return FileResponse(target, filename=target.name, headers=SANDBOX)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(x for x in target.rglob("*") if x.is_file()):
                z.write(f, f"{target.name}/{f.relative_to(target)}")
        return Response(buf.getvalue(), media_type="application/zip", headers={
            **SANDBOX, "Content-Disposition": f'attachment; filename="{target.name}.zip"'})

    @get(W + "/images/{path:path}")
    def image(code: str, path: str, branch: str | None = None):
        return FileResponse(reads.image(code, path, branch), headers=SANDBOX)

    @get(W + "/model")
    def model_(code: str, commit: str | None = None, branch: str | None = None):
        root = reads.root_of(code, branch)
        sha = model.resolve(root, commit)
        body = model.tessellation(root, sha)
        return Response(b'{"commit":"' + sha.encode() + b'","data":' + (body or b"null") + b"}",
                        media_type="application/json")

    @get(W + "/cylinders")
    def cylinders(code: str, commit: str | None = None):
        root = reads.root_of(code)
        return model.cylinders(root, model.resolve(root, commit))

    @get(W + "/fit-markers")
    def markers(code: str, commit: str | None = None, branch: str | None = None):
        c = reads.cards(code, branch, commit)
        return model.markers(reads.root_of(code, branch), c["commit"], c["results"], c["cards"])

    @get(W + "/sections/{ref}")
    def section(code: str, ref: str, commit: str | None = None, branch: str | None = None):
        root = reads.root_of(code, branch)
        if not (svg := model.section(root, model.resolve(root, commit), ref)):
            raise reads.Unknown(ref)
        return Response(svg, media_type="image/svg+xml", headers=SANDBOX)

    @post("/api/measure")
    def measure(m: Measure):
        root = reads.root_of(m.work)
        if (got := model.measure(root, model.resolve(root, m.commit), m.tool, m.paths, m.center)) is None:
            raise reads.Unknown(m.commit)
        return got

    @post(W + "/cards/{card}/decision")
    def decision(code: str, card: str, d: Decision):
        return writes.decide(code, card, **d.model_dump())

    @post(W + "/cards/{card}/revert")
    def revert(code: str, card: str, u: Undo):
        return writes.undo(code, card, **u.model_dump())

    @post(W + "/values")
    def value(code: str, v: Value):
        return writes.value(code, v.param, v.value, v.reason, v.card, v.viewed, v.branch)

    @post(W + "/model-notes")
    def note(code: str, n: Note):
        return writes.model_note(code, n.text, n.png, n.model_dump(exclude={"text", "png"}))

    @post(W + "/decisions/{did}/objection")
    def objection(code: str, did: str, r: Reason):
        return writes.objection(code, did, r.reason, r.viewed)

    @post(W + "/gates/{gate}/back")
    def gate_back(code: str, gate: str, r: Reason):
        return writes.gate_back(code, gate, r.reason, r.viewed, r.confirmed)

    @post(W + "/branches")
    def branch(code: str, b: Branch):
        return {"branch": writes.open_branch(code, b.commit, b.name)}

    @post(W + "/read-mark")
    def read_mark(code: str):
        return {"last_read": reads.read_mark(code)}

    @post("/api/works")
    def new_work(n: NewWork):
        return writes.new_work(**n.model_dump())

    @post(W + "/session")
    def open_session(code: str):
        return writes.open_session(code)

    @post(W + "/instructions")
    def instruct(code: str, x: Text):
        return writes.instruct(code, x.text)

    @post(W + "/stop")
    def stop(code: str, x: Text):
        return writes.stop(code, x.text)

    @post(W + "/resume")
    def resume(code: str):
        return writes.resume(code)

    @post(W + "/intake/answer")
    def answer(code: str, a: Answer):
        return writes.intake_answer(code, a.key, a.value)

    @app.put(W + "/inputs/{name}")
    async def upload(code: str, name: str, request: Request):
        body = await request.body()
        return await asyncio.to_thread(writes.add_input, code, name, body)

    @get("/api/events")
    async def stream_events(request: Request):
        q = events.hub.add()

        async def gen():
            try:
                yield "event: ready\ndata: {}\n\n"
                while not await request.is_disconnected():
                    try:
                        yield f"data: {await asyncio.wait_for(q.get(), KEEPALIVE)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": alive\n\n"
            finally:
                events.hub.remove(q)

        return StreamingResponse(gen(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.websocket(W + "/pty")
    async def pty(ws: WebSocket, code: str):
        """The session tab's terminal (A13, wave 2.3): loopback, allowed Host and Origin, the session cookie; the
        instruction box never writes here (§5.4 T-18a). Until the terminal exists an accepted socket closes 4501."""
        headers = {k.decode().lower(): v.decode() for k, v in ws.scope.get("headers") or []}
        if auth.refusal("GET", ws.url.path, ws.client and ws.client.host, headers, socket=True):
            await ws.close(code=WS_DENIED)
            return
        await ws.accept()
        await ws.send_json({"error": {"key": "panel.pty.later", "text": t("panel.pty.later")}})
        await ws.close(code=WS_LATER)

    @get("/{path:path}")
    def front(path: str):
        if path.startswith("api/"):
            raise reads.Unknown(path)
        base = dist().resolve()
        if not (base / "index.html").exists():
            return _error(503, "panel.front.missing", path=str(base))
        target = (base / path).resolve()
        return FileResponse(target if path and base in target.parents and target.is_file() else base / "index.html")

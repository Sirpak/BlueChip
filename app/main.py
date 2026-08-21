"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.auth.seed import seed_dev_users
from app.config import ROOT_DIR
from app.routers import admin, ask, auth, dashboard, entitlements, health, markets, models_lab
from db.session import get_session_factory

WEB_DIST = ROOT_DIR / "web" / "dist"
SPA_PAGES = (
    "desk",
    "games",
    "ask",
    "models",
    "markets",
    "research",
    "pricing",
    "teams",
    "backtests",
    "settings",
    "login",
    "admin",
    "profile",
    "account",
    "subscription",
    "usage",
    "signup",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()
    yield


app = FastAPI(
    title="BlueChipWager",
    description="NFL + CFB football intelligence desk",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGES_DIR = ROOT_DIR / "app" / "public" / "images"
if IMAGES_DIR.is_dir():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

MODELS_DIR = ROOT_DIR / "app" / "public" / "models"
if MODELS_DIR.is_dir():
    app.mount("/models", StaticFiles(directory=str(MODELS_DIR)), name="models")

app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "app" / "static")), name="static")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(markets.router)
app.include_router(models_lab.router)
app.include_router(ask.router)
app.include_router(entitlements.router)

if (WEB_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIST / "assets")), name="spa-assets")


def _png(name: str) -> FileResponse:
    return FileResponse(IMAGES_DIR / name, media_type="image/png")


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico() -> FileResponse:
    return _png("icon.png")


@app.get("/favicon.png", include_in_schema=False)
def favicon_png() -> FileResponse:
    return _png("icon.png")


@app.get("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon() -> FileResponse:
    return _png("icon_big.png")


@app.get("/site.webmanifest", include_in_schema=False)
def webmanifest() -> FileResponse:
    path = WEB_DIST / "site.webmanifest"
    if not path.is_file():
        path = ROOT_DIR / "web" / "public" / "site.webmanifest"
    return FileResponse(path, media_type="application/manifest+json")


def spa_index() -> FileResponse | HTMLResponse:
    index = WEB_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>BlueChipWager</title>"
        "<body style='font-family:sans-serif;padding:48px'>"
        "<h1>BlueChipWager</h1>"
        "<p>Build the UI, then reload.</p>"
        "<pre>cd web\nnpm install\nnpm run build</pre>"
        "<p>Or run <code>npm run dev</code> in web/ (proxies :8000).</p>",
        status_code=200,
    )


@app.get("/", response_model=None)
def spa_root() -> FileResponse | HTMLResponse:
    return spa_index()


def _register_spa_pages() -> None:
    for page in SPA_PAGES:
        app.add_api_route(
            f"/{page}",
            spa_index,
            methods=["GET"],
            include_in_schema=False,
            name=f"spa_{page}",
            response_model=None,
        )
    # model detail + admin sub-routes
    app.add_api_route(
        "/models/{model_id}",
        spa_index,
        methods=["GET"],
        include_in_schema=False,
        response_model=None,
    )
    app.add_api_route(
        "/admin/{path:path}",
        spa_index,
        methods=["GET"],
        include_in_schema=False,
        response_model=None,
    )
    app.add_api_route(
        "/pricing/{path:path}",
        spa_index,
        methods=["GET"],
        include_in_schema=False,
        response_model=None,
    )


_register_spa_pages()

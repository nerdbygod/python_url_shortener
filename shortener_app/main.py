import validators
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine
from starlette.datastructures import URL
from .config import get_settings

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"


@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.post("/url",
          response_model=schemas.URLInfo,
          response_model_exclude_unset=True,
          response_model_exclude_none=True
          )
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request("Invalid URL provided")
    if url.url_key:
        if crud.get_db_url_by_key(db=db, url_key=url.url_key, is_active=False):
            message = f"The url_key '{url.url_key}' is already taken, please use another one"
            raise_bad_request(message)
        else:
            db_url = crud.create_db_url(db=db, url=url, custom_key=url.url_key)
            return get_admin_info(db_url)
    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)


@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo
)
def get_url_info(
        secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@app.delete("/admin/{secret_key}")
def deactivate_url(
        secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)


@app.post(
    "/peek",
    name="See what's behind a shortened URL",
)
def peek_url(
        url: schemas.URLPeek, db: Session = Depends(get_db)
):
    base_url = get_settings().base_url
    if base_url in url.shortened_url:
        url_key = url.shortened_url.replace(f"{base_url}/", '')
        if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
            print(db_url)
            return {"target_url": db_url.target_url}
        else:
            message = "Target URL not found"
            raise HTTPException(status_code=404, detail=message)
    else:
        message = "Invalid domain name"
        raise_bad_request(message)

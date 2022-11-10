from pydantic import BaseModel
from fastapi import Query
from .config import get_settings


class URLBase(BaseModel):
    target_url: str
    url_key: str = Query(
        default=None,
        min_length=get_settings().url_key_min_length,
        max_length=get_settings().url_key_max_length,
        regex=r"[a-zA-Z0-9\-_]"
    )


class URL(URLBase):
    is_active: bool
    clicks: int

    class Config:
        orm_mode = True


class URLInfo(URL):
    url: str
    admin_url: str


class URLPeek(BaseModel):
    shortened_url: str = Query(default=..., max_length=256)

from pydantic import BaseModel
from fastapi import Query
from config import get_settings


class URLBase(BaseModel):
    target_url: str
    url_key: str | None


class URL(URLBase):
    is_active: bool
    clicks: int

    class Config:
        orm_mode = True


class URLInfo(URL):
    url: str
    admin_url: str


class URLPeek(BaseModel):
    shortened_url: str

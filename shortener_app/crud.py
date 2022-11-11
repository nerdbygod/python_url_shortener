from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from . import keygen, models, schemas


def get_db_url_by_key(db: Session, url_key: str, is_active: bool) -> models.URL:
    if not is_active:
        return (
            db.query(models.URL)
            .filter(models.URL.key == url_key)
            .first()
        )
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )


def get_db_url_by_secret_key(db: Session, secret_key: str, is_active: bool) -> models.URL:
    if is_active:
        return (
            db.query(models.URL)
            .filter(models.URL.secret_key == secret_key, models.URL.is_active)
            .first()
        )
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key)
        .first()
    )


def create_db_url(db: Session, url: schemas.URLBase, custom_key: str = None) -> models.URL:
    def _add_record_to_db(database):
        db.add(database)
        db.commit()
        db.refresh(database)

    if custom_key:
        secret_key = f"{custom_key}_{keygen.create_random_key(8)}"
        db_url = models.URL(
            target_url=url.target_url, key=custom_key, secret_key=secret_key
        )
        _add_record_to_db(database=db_url)
        return db_url
    key = keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(8)}"
    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    _add_record_to_db(database=db_url)
    return db_url


def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db_url.last_clicked_at = func.now()
    db.commit()
    db.refresh(db_url)
    return db_url


# The deactivation and activation functions might need refactoring to avoid code repetition
def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key, is_active=True)
    if db_url:
        db_url.is_active = False
        db_url.deactivated_at = func.now()
        db.commit()
        db.refresh(db_url)
    return db_url


def reactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key, is_active=False)
    if db_url:
        db_url.is_active = True
        db_url.deactivated_at = None
        db.commit()
        db.refresh(db_url)
    return db_url

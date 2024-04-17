import os
import sqlite3
from sqlite3 import Connection
from datetime import datetime

import click
from flask import current_app, g, abort, url_for

import qrcode
from qrcode.image.svg import SvgImage


class User:
    def __init__(self, id: int, username: str, created_at: str):
        self.id = id
        self.username = username
        self.created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

    def get_qr_codes(self):
        qr_ids = get_db().execute(
            "SELECT id FROM qr_code WHERE user_id = ?", (self.id,)
        )

        return (QRCode.from_id(id["id"]) for id in qr_ids)

    def get_qr_code_pings(self):
        import itertools

        return itertools.chain(*(qr.get_qr_code_pings() for qr in self.get_qr_codes()))

    @classmethod
    def from_id(cls, id: int):
        user = get_db().execute("SELECT * FROM user WHERE id = ?", (id,)).fetchone()

        return cls(user["id"], user["username"], user["created_at"])

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, created_at={self.created_at})"


class QRCode:
    def __init__(self, id: int, user_id: int, description: str, created_at: str):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        self._generate_svg_if_not_exists()

    def get_qr_code_pings(self):
        ping_ids = get_db().execute(
            "SELECT id FROM qr_code_ping WHERE qr_code_id = ?", (self.id,)
        )

        return (QRCodePing.from_id(id["id"]) for id in ping_ids)

    def svg_path(self):
        return os.path.join(
            current_app.root_path, "static", "qr_images", f"{self.id}.svg"
        )

    def svg_url(self):
        return url_for("static", filename=f"qr_images/{self.id}.svg")

    def _generate_svg_if_not_exists(self):
        if os.path.exists(self.svg_path()):
            return

        qr = qrcode.QRCode(
            version=1, error_correction=qrcode.ERROR_CORRECT_H, image_factory=SvgImage
        )

        data = f"findq.francisdb.net/p/{self.id}"
        qr.add_data(data)

        img = qr.make_image()
        svg_bytes = img.to_string()

        with open(
            self.svg_path(),
            "wb",
        ) as f:
            f.write(svg_bytes)

    @classmethod
    def from_id(cls, id: int):
        qr = get_db().execute("SELECT * FROM qr_code WHERE id = ?", (id,)).fetchone()
        return cls(qr["id"], qr["user_id"], qr["description"], qr["created_at"])

    @staticmethod
    def create(user_id: int, description: str):
        db = get_db()
        db.execute(
            "INSERT INTO qr_code (user_id, description) VALUES (?, ?)",
            (user_id, description),
        )

        db.commit()

    def __repr__(self):
        return f"QRCode(id={self.id}, user_id={self.user_id}, description={self.description}, created_at={self.created_at})"


class QRCodePing:
    def __init__(
        self, id: int, qr_code_id: int, lat: float, lon: float, created_at: str
    ):
        self.id = id
        self.qr_code_id = qr_code_id
        self.lat = lat
        self.lon = lon
        self.created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

    def get_qr_code(self):
        return QRCode.from_id(self.qr_code_id)

    @classmethod
    def from_id(cls, id: int):
        ping = (
            get_db()
            .execute("SELECT * FROM qr_code_ping WHERE id = ?", (id,))
            .fetchone()
        )

        return cls(
            id=ping["id"],
            qr_code_id=ping["qr_code_id"],
            lat=ping["lat"],
            lon=ping["lon"],
            created_at=ping["created_at"],
        )

    @staticmethod
    def create(qr_code_id: int, lat: float, lon: float):
        db = get_db()

        db.execute(
            "INSERT INTO qr_code_ping (qr_code_id, lat, lon) VALUES (?, ?, ?)",
            (qr_code_id, lat, lon),
        )

        db.commit()

    def __repr__(self):
        return f"QRCodePing(id={self.id}, qr_code_id={self.qr_code_id}, lat={self.lat}, lon={self.lon}, created_at={self.created_at})"


def create_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("create-db")
def create_db_command():
    create_db()
    click.echo("Database created.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(create_db_command)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

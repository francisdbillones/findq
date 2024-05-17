from datetime import datetime

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from findq.auth import login_required
from findq.db_utils import get_db, User, QRCode, QRCodePing
from findq.utils import generate_gmaps_embed_link

bp = Blueprint("qr", __name__)


@bp.route("/")
@login_required
def index():
    """Show all the QR code pings, most recent first."""
    from datetime import datetime

    user = User.from_id(g.user["id"])

    recent_ping_id = (
        get_db()
        .execute("SELECT id FROM qr_code_ping ORDER BY created_at DESC LIMIT 1")
        .fetchone()
    )["id"]
    recent_ping = QRCodePing.from_id(recent_ping_id)

    if recent_ping is not None:
        gmaps_embed_link = generate_gmaps_embed_link(
            recent_ping.lat, recent_ping.lon, 15
        )
        strftime_string = "%-I:%M %p, %B %-d, %Y"
        recent_ping_title = (
            f"Ping made on {recent_ping.created_at.strftime(strftime_string)}."
        )
        image_urls = [
            url_for(
                "static",
                filename=f"qr_ping_images/{image.id}.png",
            )
            for image in recent_ping.get_images()
        ]
        gmaps_link = (
            f"https://www.google.com/maps?q={recent_ping.lat},{recent_ping.lon}"
        )

        return render_template(
            "qr/index.html",
            user=user,
            gmaps_embed_link=gmaps_embed_link,
            recent_ping_title=recent_ping_title,
            image_urls=image_urls,
            gmaps_link=gmaps_link,
        )
    else:
        return render_template("qr/index.html", user=user)


@bp.route("/view_qr_codes", methods=("GET", "POST"))
@login_required
def view_qr_codes():
    """View QR codes for the current user."""

    qr_code_ids = get_db().execute(
        "SELECT id FROM qr_code WHERE user_id = ?", (g.user["id"],)
    )
    qr_codes = [QRCode.from_id(qr_code_id["id"]) for qr_code_id in qr_code_ids]

    return render_template("qr/view_qr_code.html", qr_codes=qr_codes)


@bp.route("/view_ping/<int:qr_code_ping_id>")
def view_qr_code_ping(qr_code_ping_id: int):
    import os

    qr_code_ping = QRCodePing.from_id(qr_code_ping_id)
    lat = qr_code_ping.lat
    lon = qr_code_ping.lon
    zoom = 15

    gmaps_embed_link = generate_gmaps_embed_link(lat, lon, zoom)

    strftime_string = "%-I:%M %p, %B %-d, %Y"
    qr_code_ping_title = (
        # format it like 8:32 PM, August 1, 2021
        # generate strftime
        f"Ping made on {qr_code_ping.created_at.strftime(strftime_string)}."
    )
    qr_code_ping_description = qr_code_ping.description
    gmaps_link = f"https://www.google.com/maps?q={lat},{lon}"

    images = qr_code_ping.get_images()
    image_urls = [
        url_for("static", filename=os.path.join("qr_ping_images", f"{image.id}.png"))
        for image in images
    ]

    return render_template(
        "qr/view_qr_code_ping.html",
        gmaps_embed_link=gmaps_embed_link,
        qr_code_ping_title=qr_code_ping_title,
        qr_code_ping_description=qr_code_ping_description,
        gmaps_link=gmaps_link,
        image_urls=image_urls,
    )


@bp.route("/view_qr_code_pings/")
@login_required
def view_qr_code_pings():
    """View QR code pings for the current user."""
    user = User.from_id(g.user["id"])

    qr_code_pings = sorted(
        user.get_qr_code_pings(), key=lambda ping: ping.created_at, reverse=True
    )

    for ping in qr_code_pings:
        qr_code = QRCode.from_id(ping.qr_code_id)
        gmaps_embed_link = generate_gmaps_embed_link(ping.lat, ping.lon, 15)
        ping.title = f"'{qr_code.description}' pinged on {ping.created_at.strftime('%-I:%M %p, %B %-d, %Y')}"
        ping.gmaps_embed_link = gmaps_embed_link

    return render_template("qr/view_qr_code_pings.html", qr_code_pings=qr_code_pings)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create_qr_code():
    """Create a new QR code for the current user."""
    if request.method == "POST":
        description = request.form["description"]
        error = None

        if not description:
            error = "Description is required."

        if error is not None:
            flash(error)
        else:
            QRCode.create(g.user["id"], description)
            return redirect(url_for("qr.index"))

    return render_template("qr/create_qr_code.html")


@bp.route("/p/<int:qr_code_id>", methods=["GET", "POST"])
def create_qr_code_ping(qr_code_id: int):
    qr_code = QRCode.from_id(qr_code_id)

    if request.method == "GET":
        return render_template("qr/create_qr_code_ping.html", qr_code=qr_code)

    lat = float(request.form["lat"])
    lon = float(request.form["lon"])
    description = request.form["description"]

    images = request.files.getlist("images")

    QRCodePing.create(qr_code_id, lat, lon, description, images)

    return redirect(url_for("qr.thank_you"))


@bp.route("/thank_you")
def thank_you():
    return render_template("qr/thank_you.html")


@bp.route("/download_qr_code/<int:qr_code_id>")
def download_qr_code(qr_code_id: int):
    from flask import send_file, current_app
    import os

    return send_file(
        os.path.join(
            current_app.root_path,
            "static",
            "qr_images",
            f"{qr_code_id}.png",
        ),
        as_attachment=True,
    )

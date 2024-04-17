from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from findq.auth import login_required
from findq.db_utils import User, QRCode, QRCodePing
from findq.utils import generate_gmaps_embed_link

bp = Blueprint("qr", __name__)


@bp.route("/")
@login_required
def index():
    """Show all the QR code pings, most recent first."""
    user = User.from_id(g.user["id"])

    return render_template("qr/index.html", user=user)


@bp.route("/<int:id>", methods=("GET", "POST"))
@login_required
def view_qr_code(id: int):
    """View a QR code"""

    qr_code = QRCode.from_id(id)

    return render_template("qr/view_qr_code.html", qr_code=qr_code)


@bp.route("/view_ping/<int:qr_code_ping_id>")
def view_qr_code_ping(qr_code_ping_id: int):
    qr_code_ping = QRCodePing.from_id(qr_code_ping_id)
    lat = qr_code_ping.lat
    lon = qr_code_ping.lon
    zoom = 15
    return render_template(
        "qr/view_qr_code_ping.html",
        gmaps_embed_link=generate_gmaps_embed_link(lat, lon, zoom),
    )


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
            QRCode.create(g["user"].id, description)
            return redirect(url_for("qr.index"))

    return render_template("qr/create_qr_code.html")


@bp.route("/p/<int:qr_code_id>", methods=["GET", "POST"])
def create_qr_code_ping(qr_code_id: int):
    qr_code = QRCode.from_id(qr_code_id)

    if request.method == "GET":
        return render_template("qr/create_qr_code_ping.html", qr_code=qr_code)

    lat = float(request.form["lat"])
    lon = float(request.form["lon"])

    QRCodePing.create(qr_code_id, lat, lon)

    return redirect(url_for("qr.thank_you"))


@bp.route("/thank_you")
def thank_you():
    return render_template("qr/thank_you.html")

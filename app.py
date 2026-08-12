from flask import Flask, render_template, request, abort, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "rates.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def home():

    results = []
    vehicle_price = None
    salalah_shihen_fee = None

    if request.method == "POST":

        search = request.form.get("search", "")

        search = " ".join(search.strip().upper().split())

        conn = get_connection()

        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM rates
            WHERE
                UPPER(BRANCH) LIKE ?
                OR UPPER(CITY) LIKE ?
            ORDER BY STATE, BRANCH
        """, (f"%{search}%", f"%{search}%"))

        rows = cur.fetchall()

        vehicle_price = request.form.get("vehicle_price", "").strip()

        try:
            vehicle_price = float(vehicle_price)
        except:
            vehicle_price = None

        salalah_shihen_fee = request.form.get("salalah_shihen_fee", "").strip()

        try:
            salalah_shihen_fee = float(salalah_shihen_fee)
        except:
            salalah_shihen_fee = None

        results = []

        for row in rows:

            row = dict(row)

            towing = float(row["TOWING RATE"])
            ocean40 = float(row["SHIPPING RATE 40 HC"])
            ocean45 = float(row["SHIPPING RATE 45 HC"])

            shipping40 = towing + ocean40
            shipping45 = towing + ocean45

            total40 = shipping40
            total45 = shipping45

            if vehicle_price is not None:
                total40 += vehicle_price
                total45 += vehicle_price

            if salalah_shihen_fee is not None:
                total40 += salalah_shihen_fee
                total45 += salalah_shihen_fee

            row["OCEAN40"] = ocean40
            row["OCEAN45"] = ocean45
            row["SHIPPING40"] = shipping40
            row["SHIPPING45"] = shipping45
            row["TOTAL40"] = total40
            row["TOTAL45"] = total45
            row["VEHICLE_PRICE"] = vehicle_price
            row["SALALAH_SHIHEN_FEE"] = salalah_shihen_fee

            results.append(row)

        conn.close()

    return render_template(
        "index.html",
        results=results,
        vehicle_price=vehicle_price,
        salalah_shihen_fee=salalah_shihen_fee
    )


@app.route("/estimate/<int:id>")
def estimate(id):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM rates WHERE ID=?",
        (id,)
    )

    row = cur.fetchone()

    conn.close()

    if row is None:
        abort(404)

    return render_template(
        "estimate.html",
        row=row
    )


@app.route("/api/search")
def api_search():

    q = request.args.get("q", "").strip().upper()

    if len(q) < 2:
        return jsonify([])

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT ID,
               BRANCH,
               CITY,
               STATE,
               WAREHOUSE
        FROM rates
        WHERE
            UPPER(BRANCH) LIKE ?
            OR UPPER(CITY) LIKE ?
        ORDER BY BRANCH
        LIMIT 10
    """, (f"%{q}%", f"%{q}%"))

    rows = [dict(r) for r in cur.fetchall()]

    conn.close()

    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True)

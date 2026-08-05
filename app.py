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

        results = []

        for row in rows:

            row = dict(row)

            towing = float(row["TOWING RATE"])
            ocean40 = float(row["SHIPPING RATE 40 HC"])
            ocean45 = float(row["SHIPPING RATE 45 HC"])

            shipping40 = towing + ocean40
            shipping45 = towing + ocean45

            if vehicle_price is None:
                total40 = shipping40
                total45 = shipping45
            else:
                total40 = shipping40 + vehicle_price
                total45 = shipping45 + vehicle_price

            row["OCEAN40"] = ocean40
            row["OCEAN45"] = ocean45
            row["SHIPPING40"] = shipping40
            row["SHIPPING45"] = shipping45
            row["TOTAL40"] = total40
            row["TOTAL45"] = total45
            row["VEHICLE_PRICE"] = vehicle_price

            results.append(row)

        conn.close()

    return render_template(
        "index.html",
        results=results,
        vehicle_price=vehicle_price
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

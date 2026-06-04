"""
Railway Reservation Management System
Backend: Python Flask
Database: MySQL
"""

from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import os
from datetime import date

app = Flask(__name__, template_folder="../frontend")
app.secret_key = "railway_secret_key_2024"
CORS(app, supports_credentials=True)

@app.route("/")
def home():
    return render_template("index.html")

# ============================================
# DATABASE CONNECTION
# ============================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # Change to your MySQL username
    "password": "1234",          # Change to your MySQL password
    "database": "railway_db"
}

def get_db():
    """Get a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database error: {e}")
        return None

def hash_password(password):
    """Simple password hashing using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================
# PASSENGER ROUTES
# ============================================

@app.route("/api/passenger/register", methods=["POST"])
def register_passenger():
    """Register a new passenger."""
    data = request.json
    required = ["name", "age", "gender", "phone_no", "password"]
    
    for field in required:
        if not data.get(field):
            return jsonify({"success": False, "message": f"'{field}' is required."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        hashed_pw = hash_password(data["password"])
        cursor.execute("""
            INSERT INTO passenger (name, age, gender, phone_no, authentication_password)
            VALUES (%s, %s, %s, %s, %s)
        """, (data["name"], data["age"], data["gender"], data["phone_no"], hashed_pw))
        conn.commit()
        passenger_id = cursor.lastrowid
        return jsonify({"success": True, "message": "Passenger registered successfully!", "passenger_id": passenger_id}), 201
    except Error as e:
        if "Duplicate entry" in str(e):
            return jsonify({"success": False, "message": "Phone number already registered."}), 409
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/passenger/login", methods=["POST"])
def login_passenger():
    """Authenticate a passenger (CHECK relationship in ER)."""
    data = request.json
    if not data.get("phone_no") or not data.get("password"):
        return jsonify({"success": False, "message": "Phone number and password required."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        hashed_pw = hash_password(data["password"])
        cursor.execute("""
            SELECT passenger_id, name, age, gender, phone_no
            FROM passenger
            WHERE phone_no = %s AND authentication_password = %s
        """, (data["phone_no"], hashed_pw))
        passenger = cursor.fetchone()

        if passenger:
            session["passenger_id"] = passenger["passenger_id"]
            session["role"] = "passenger"
            return jsonify({"success": True, "message": "Login successful!", "passenger": passenger})
        else:
            return jsonify({"success": False, "message": "Invalid phone number or password."}), 401
    finally:
        cursor.close()
        conn.close()


@app.route("/api/passenger/<int:passenger_id>", methods=["GET"])
def get_passenger(passenger_id):
    """Get passenger details."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT passenger_id, name, age, gender, phone_no
            FROM passenger WHERE passenger_id = %s
        """, (passenger_id,))
        passenger = cursor.fetchone()
        if passenger:
            return jsonify({"success": True, "passenger": passenger})
        return jsonify({"success": False, "message": "Passenger not found."}), 404
    finally:
        cursor.close()
        conn.close()


# ============================================
# TRAIN DETAIL ROUTES
# ============================================

@app.route("/api/trains", methods=["GET"])
def get_all_trains():
    """Get all trains."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM train_detail")
        trains = cursor.fetchall()
        return jsonify({"success": True, "trains": trains})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/trains/search", methods=["GET"])
def search_trains():
    """Search trains by source and destination."""
    source = request.args.get("source", "")
    destination = request.args.get("destination", "")

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM train_detail
            WHERE reservation_halting LIKE %s AND reservation_halting LIKE %s
        """, (f"%{source}%", f"%{destination}%"))
        trains = cursor.fetchall()
        return jsonify({"success": True, "trains": trains})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/trains/<train_no>", methods=["GET"])
def get_train(train_no):
    """Get a single train's details."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM train_detail WHERE train_no = %s", (train_no,))
        train = cursor.fetchone()
        if train:
            return jsonify({"success": True, "train": train})
        return jsonify({"success": False, "message": "Train not found."}), 404
    finally:
        cursor.close()
        conn.close()


# ============================================
# TICKET ROUTES (ISSUE relationship in ER)
# ============================================

@app.route("/api/ticket/book", methods=["POST"])
def book_ticket():
    """
    Book a ticket - implements the ISSUE relationship between Passenger and Ticket.
    Also triggers payment creation (DONE / PAYMENT flow).
    """
    data = request.json
    required = ["source", "destination", "no_of_passengers", "date", "train_no", "passenger_id"]
    
    for field in required:
        if not data.get(field):
            return jsonify({"success": False, "message": f"'{field}' is required."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify passenger exists
        cursor.execute("SELECT * FROM passenger WHERE passenger_id = %s", (data["passenger_id"],))
        passenger = cursor.fetchone()
        if not passenger:
            return jsonify({"success": False, "message": "Passenger not found."}), 404

        # Verify train exists
        cursor.execute("SELECT * FROM train_detail WHERE train_no = %s", (data["train_no"],))
        train = cursor.fetchone()
        if not train:
            return jsonify({"success": False, "message": "Train not found."}), 404

        # Insert ticket
        cursor.execute("""
            INSERT INTO ticket (source, destination, no_of_passengers, date, reservation_general, train_no, passenger_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["source"],
            data["destination"],
            data["no_of_passengers"],
            data["date"],
            data.get("reservation_general", "General"),
            data["train_no"],
            data["passenger_id"]
        ))
        conn.commit()
        ticket_id = cursor.lastrowid

        # Calculate fare (simple: 500 per person per compartment type)
        fare_map = {
            "AC Chair Car": 800,
            "AC 3-Tier": 1200,
            "Sleeper": 400,
            "Second Sitting": 200
        }
        base_fare = fare_map.get(train["compartment"], 500)
        total_amount = base_fare * int(data["no_of_passengers"])

        # Create pending payment record
        cursor.execute("""
            INSERT INTO payment (ticket_id, total_amount, on_time_payment, payment_status)
            VALUES (%s, %s, %s, %s)
        """, (ticket_id, total_amount, "Yes", "Pending"))
        conn.commit()
        payment_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Ticket booked successfully!",
            "ticket_id": ticket_id,
            "payment_id": payment_id,
            "total_amount": total_amount
        }), 201

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/ticket/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Get ticket details with train and passenger info."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, p.name AS passenger_name, p.phone_no,
                   td.train_name, td.compartment,
                   pay.payment_id, pay.total_amount, pay.payment_status, pay.on_time_payment
            FROM ticket t
            JOIN passenger p ON t.passenger_id = p.passenger_id
            JOIN train_detail td ON t.train_no = td.train_no
            LEFT JOIN payment pay ON pay.ticket_id = t.ticket_id
            WHERE t.ticket_id = %s
        """, (ticket_id,))
        ticket = cursor.fetchone()
        if ticket:
            # Convert date to string
            if ticket.get("date"):
                ticket["date"] = str(ticket["date"])
            return jsonify({"success": True, "ticket": ticket})
        return jsonify({"success": False, "message": "Ticket not found."}), 404
    finally:
        cursor.close()
        conn.close()


@app.route("/api/tickets/passenger/<int:passenger_id>", methods=["GET"])
def get_passenger_tickets(passenger_id):
    """Get all tickets for a passenger."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, td.train_name, td.compartment,
                   pay.total_amount, pay.payment_status
            FROM ticket t
            JOIN train_detail td ON t.train_no = td.train_no
            LEFT JOIN payment pay ON pay.ticket_id = t.ticket_id
            WHERE t.passenger_id = %s
            ORDER BY t.ticket_id DESC
        """, (passenger_id,))
        tickets = cursor.fetchall()
        for ticket in tickets:
            if ticket.get("date"):
                ticket["date"] = str(ticket["date"])
        return jsonify({"success": True, "tickets": tickets})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/ticket/<int:ticket_id>/cancel", methods=["DELETE"])
def cancel_ticket(ticket_id):
    """Cancel a ticket."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        # Delete payment first (FK constraint)
        cursor.execute("DELETE FROM payment WHERE ticket_id = %s", (ticket_id,))
        cursor.execute("DELETE FROM ticket WHERE ticket_id = %s", (ticket_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "Ticket cancelled successfully."})
        return jsonify({"success": False, "message": "Ticket not found."}), 404
    finally:
        cursor.close()
        conn.close()


# ============================================
# PAYMENT ROUTES (PAYMENT entity in ER)
# ============================================

@app.route("/api/payment/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    """Get payment details."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payment WHERE payment_id = %s", (payment_id,))
        payment = cursor.fetchone()
        if payment:
            return jsonify({"success": True, "payment": payment})
        return jsonify({"success": False, "message": "Payment not found."}), 404
    finally:
        cursor.close()
        conn.close()


@app.route("/api/payment/<int:payment_id>/complete", methods=["PUT"])
def complete_payment(payment_id):
    """
    Complete a payment - implements DONE relationship in ER diagram.
    """
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE payment
            SET payment_status = 'Done', on_time_payment = 'Yes'
            WHERE payment_id = %s
        """, (payment_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "Payment completed successfully!"})
        return jsonify({"success": False, "message": "Payment not found."}), 404
    finally:
        cursor.close()
        conn.close()


# ============================================
# SUPERVISOR ROUTES (MANAGE relationship in ER)
# ============================================

@app.route("/api/supervisor/login", methods=["POST"])
def login_supervisor():
    """Authenticate technical supervisor."""
    data = request.json
    if not data.get("email") or not data.get("password"):
        return jsonify({"success": False, "message": "Email and password required."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        hashed_pw = hash_password(data["password"])
        cursor.execute("""
            SELECT supervisor_id, name, email, phone_no
            FROM technical_supervisor
            WHERE email = %s AND authentication_password = %s
        """, (data["email"], hashed_pw))
        supervisor = cursor.fetchone()
        if supervisor:
            session["supervisor_id"] = supervisor["supervisor_id"]
            session["role"] = "supervisor"
            return jsonify({"success": True, "message": "Supervisor login successful!", "supervisor": supervisor})
        return jsonify({"success": False, "message": "Invalid credentials."}), 401
    finally:
        cursor.close()
        conn.close()


@app.route("/api/supervisor/trains", methods=["GET"])
def supervisor_get_trains():
    """Supervisor: view all trains (MANAGE relationship)."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM train_detail")
        trains = cursor.fetchall()
        return jsonify({"success": True, "trains": trains})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/supervisor/trains", methods=["POST"])
def supervisor_add_train():
    """Supervisor: add a new train (MANAGE relationship)."""
    data = request.json
    required = ["train_no", "train_name", "compartment"]
    for field in required:
        if not data.get(field):
            return jsonify({"success": False, "message": f"'{field}' is required."}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO train_detail (train_no, train_name, compartment, reservation_halting, train_halt_at_station, reservation_chart)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["train_no"], data["train_name"], data["compartment"],
            data.get("reservation_halting", ""),
            data.get("train_halt_at_station", ""),
            data.get("reservation_chart", "Available")
        ))
        conn.commit()
        return jsonify({"success": True, "message": "Train added successfully!"}), 201
    except Error as e:
        if "Duplicate entry" in str(e):
            return jsonify({"success": False, "message": "Train number already exists."}), 409
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/supervisor/trains/<train_no>", methods=["PUT"])
def supervisor_update_train(train_no):
    """Supervisor: update train details."""
    data = request.json
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE train_detail
            SET train_name=%s, compartment=%s, reservation_halting=%s,
                train_halt_at_station=%s, reservation_chart=%s
            WHERE train_no=%s
        """, (
            data.get("train_name"), data.get("compartment"),
            data.get("reservation_halting"), data.get("train_halt_at_station"),
            data.get("reservation_chart"), train_no
        ))
        conn.commit()
        return jsonify({"success": True, "message": "Train updated successfully!"})
    finally:
        cursor.close()
        conn.close()


@app.route("/api/supervisor/trains/<train_no>", methods=["DELETE"])
def supervisor_delete_train(train_no):
    """Supervisor: delete a train."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM train_detail WHERE train_no = %s", (train_no,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "Train deleted."})
        return jsonify({"success": False, "message": "Train not found."}), 404
    finally:
        cursor.close()
        conn.close()


@app.route("/api/supervisor/all-tickets", methods=["GET"])
def supervisor_all_tickets():
    """Supervisor: view all tickets."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed."}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, p.name AS passenger_name, p.phone_no,
                   td.train_name, pay.total_amount, pay.payment_status
            FROM ticket t
            JOIN passenger p ON t.passenger_id = p.passenger_id
            JOIN train_detail td ON t.train_no = td.train_no
            LEFT JOIN payment pay ON pay.ticket_id = t.ticket_id
            ORDER BY t.ticket_id DESC
        """)
        tickets = cursor.fetchall()
        for t in tickets:
            if t.get("date"):
                t["date"] = str(t["date"])
        return jsonify({"success": True, "tickets": tickets})
    finally:
        cursor.close()
        conn.close()


# ============================================
# HEALTH CHECK
# ============================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "Railway API is running!"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

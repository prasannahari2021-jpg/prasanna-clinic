import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_number TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT,
            pet_name TEXT NOT NULL,
            pet_type TEXT NOT NULL,
            breed TEXT NOT NULL,
            age TEXT NOT NULL,
            gender TEXT NOT NULL,
            weight TEXT NOT NULL,
            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS owner_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_name TEXT NOT NULL DEFAULT 'Prasanna Pet Care Clinic',
            clinic_logo TEXT,
            home_banner TEXT,
            dashboard_banner TEXT,
            contact_number TEXT NOT NULL DEFAULT '+91 9342301937',
            email_address TEXT NOT NULL DEFAULT 'clinic@prasannapetcare.com',
            clinic_address TEXT NOT NULL DEFAULT '#62 SNS College Coimbatore',
            opening_hours TEXT NOT NULL DEFAULT '24/7 Emergency Care',
            theme_color TEXT NOT NULL DEFAULT '#10b981',
            announcement_banner TEXT,
            home_images TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def generate_token() -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(token_number, 4) AS INTEGER)) AS max_num FROM appointments"
    ).fetchone()
    conn.close()

    max_num = row["max_num"] if row and row["max_num"] is not None else 0
    next_num = max_num + 1
    if next_num < 10000:
        return f"TKN{next_num:04d}"
    return f"TKN{next_num}"


def normalize_status(value: Optional[str]) -> str:
    status = (value or "Pending").strip().title()
    allowed = {"Pending", "Confirmed", "Completed", "Cancelled"}
    return status if status in allowed else "Pending"


def appointment_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "token_number": row["token_number"],
        "owner_name": row["owner_name"],
        "mobile": row["mobile"],
        "email": row["email"],
        "pet_name": row["pet_name"],
        "pet_type": row["pet_type"],
        "breed": row["breed"],
        "age": row["age"],
        "gender": row["gender"],
        "weight": row["weight"],
        "service": row["service"],
        "appointment_date": row["appointment_date"],
        "appointment_time": row["appointment_time"],
        "symptoms": row["symptoms"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def create_appointment(data: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = [
        "owner_name",
        "mobile",
        "pet_name",
        "pet_type",
        "breed",
        "age",
        "gender",
        "weight",
        "service",
        "appointment_date",
        "appointment_time",
    ]
    missing = [field for field in required_fields if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    token = generate_token()
    payload = {
        "token_number": token,
        "owner_name": data.get("owner_name", "").strip(),
        "mobile": data.get("mobile", "").strip(),
        "email": (data.get("email") or "").strip() or None,
        "pet_name": data.get("pet_name", "").strip(),
        "pet_type": data.get("pet_type", "").strip(),
        "breed": data.get("breed", "").strip(),
        "age": data.get("age", "").strip(),
        "gender": data.get("gender", "").strip(),
        "weight": data.get("weight", "").strip(),
        "service": data.get("service", "").strip(),
        "appointment_date": data.get("appointment_date", "").strip(),
        "appointment_time": data.get("appointment_time", "").strip(),
        "symptoms": data.get("symptoms", "").strip(),
        "status": "Pending",
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }

    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO appointments (
            token_number,
            owner_name,
            mobile,
            email,
            pet_name,
            pet_type,
            breed,
            age,
            gender,
            weight,
            service,
            appointment_date,
            appointment_time,
            symptoms,
            status,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["token_number"],
            payload["owner_name"],
            payload["mobile"],
            payload["email"],
            payload["pet_name"],
            payload["pet_type"],
            payload["breed"],
            payload["age"],
            payload["gender"],
            payload["weight"],
            payload["service"],
            payload["appointment_date"],
            payload["appointment_time"],
            payload["symptoms"],
            payload["status"],
            payload["created_at"],
        ),
    )
    conn.commit()
    appointment_id = cursor.lastrowid
    conn.close()
    payload["id"] = appointment_id
    return payload


def get_appointments(filters: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
    conn = get_connection()
    query = "SELECT * FROM appointments"
    clauses = []
    values: list[Any] = []

    filters = filters or {}
    search = (filters.get("search") or "").strip()
    if search:
        clauses.append(
            "(owner_name LIKE ? OR token_number LIKE ? OR pet_name LIKE ? OR mobile LIKE ?)"
        )
        like_value = f"%{search}%"
        values.extend([like_value, like_value, like_value, like_value])

    status = (filters.get("status") or "").strip()
    if status:
        clauses.append("status = ?")
        values.append(status)

    date_filter = (filters.get("date_filter") or "").strip()
    if date_filter:
        if date_filter == "today":
            clauses.append("appointment_date = ?")
            values.append(datetime.utcnow().strftime("%Y-%m-%d"))
        elif date_filter == "tomorrow":
            tomorrow = (datetime.utcnow().date() + timedelta(days=1)).strftime("%Y-%m-%d")
            clauses.append("appointment_date = ?")
            values.append(tomorrow)
        elif date_filter == "this_week":
            clauses.append("appointment_date BETWEEN ? AND ?")
            start = datetime.utcnow().date().strftime("%Y-%m-%d")
            end = (datetime.utcnow().date() + timedelta(days=6)).strftime("%Y-%m-%d")
            values.extend([start, end])

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, values).fetchall()
    conn.close()
    return [appointment_from_row(row) for row in rows]


def get_appointment_by_id(appointment_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
    conn.close()
    return appointment_from_row(row) if row else None


def get_appointment_by_token(token_number: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM appointments WHERE token_number = ?", (token_number,)).fetchone()
    conn.close()
    return appointment_from_row(row) if row else None


def update_appointment(appointment_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not updates:
        return get_appointment_by_id(appointment_id)

    allowed = {
        "owner_name",
        "mobile",
        "email",
        "pet_name",
        "pet_type",
        "breed",
        "age",
        "gender",
        "weight",
        "service",
        "appointment_date",
        "appointment_time",
        "symptoms",
        "status",
    }
    filtered_updates = {key: value for key, value in updates.items() if key in allowed}
    if not filtered_updates:
        return get_appointment_by_id(appointment_id)

    if "status" in filtered_updates:
        filtered_updates["status"] = normalize_status(filtered_updates["status"])

    assignments = ", ".join([f"{key} = ?" for key in filtered_updates.keys()])
    values = [value for value in filtered_updates.values()]
    values.append(appointment_id)

    conn = get_connection()
    conn.execute(f"UPDATE appointments SET {assignments} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_appointment_by_id(appointment_id)


def delete_appointment(appointment_id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def get_dashboard_stats() -> Dict[str, int]:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) AS count FROM appointments").fetchone()["count"]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    todays = conn.execute(
        "SELECT COUNT(*) AS count FROM appointments WHERE appointment_date = ?",
        (today,),
    ).fetchone()["count"]
    pending = conn.execute("SELECT COUNT(*) AS count FROM appointments WHERE status = 'Pending'").fetchone()["count"]
    completed = conn.execute("SELECT COUNT(*) AS count FROM appointments WHERE status = 'Completed'").fetchone()["count"]
    cancelled = conn.execute("SELECT COUNT(*) AS count FROM appointments WHERE status = 'Cancelled'").fetchone()["count"]
    conn.close()
    return {
        "total": total,
        "today": todays,
        "pending": pending,
        "completed": completed,
        "cancelled": cancelled,
    }


def get_owner_settings() -> Dict[str, Any]:
    conn = get_connection()
    settings = conn.execute("SELECT * FROM owner_settings ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if not settings:
        return {
            "clinic_name": "Prasanna Pet Care Clinic",
            "clinic_logo": "",
            "home_banner": "",
            "dashboard_banner": "",
            "contact_number": "+91 9342301937",
            "email_address": "clinic@prasannapetcare.com",
            "clinic_address": "#62 SNS College Coimbatore",
            "opening_hours": "24/7 Emergency Care",
            "theme_color": "#10b981",
            "announcement_banner": "",
            "home_images": "",
        }
    return {key: settings[key] for key in settings.keys()}


def save_owner_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    conn.execute("DELETE FROM owner_settings")
    conn.execute(
        """
        INSERT INTO owner_settings (
            clinic_name,
            clinic_logo,
            home_banner,
            dashboard_banner,
            contact_number,
            email_address,
            clinic_address,
            opening_hours,
            theme_color,
            announcement_banner,
            home_images
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("clinic_name", "Prasanna Pet Care Clinic").strip(),
            (data.get("clinic_logo") or "").strip(),
            (data.get("home_banner") or "").strip(),
            (data.get("dashboard_banner") or "").strip(),
            (data.get("contact_number") or "+91 9342301937").strip(),
            (data.get("email_address") or "clinic@prasannapetcare.com").strip(),
            (data.get("clinic_address") or "#62 SNS College Coimbatore").strip(),
            (data.get("opening_hours") or "24/7 Emergency Care").strip(),
            (data.get("theme_color") or "#10b981").strip(),
            (data.get("announcement_banner") or "").strip(),
            (data.get("home_images") or "").strip(),
        ),
    )
    conn.commit()
    conn.close()
    return get_owner_settings()

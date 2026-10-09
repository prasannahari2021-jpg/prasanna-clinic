from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, session

from database import (
    create_appointment,
    delete_appointment,
    get_appointment_by_id,
    get_appointment_by_token,
    get_appointments,
    get_dashboard_stats,
    get_owner_settings,
    init_db,
    save_owner_settings,
    update_appointment,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "prasanna-clinic-secret"

SERVICES_CATALOG = [
    {
        "id": "srv-1",
        "name": "Comprehensive Canine Wellness & Checkup",
        "category": "dogs",
        "categoryLabel": "For Dogs 🐶",
        "price": "₹799 / $25",
        "image": "https://images.unsplash.com/photo-1548767797-d8c844163c4c?auto=format&fit=crop&w=600&q=80",
        "description": "Full head-to-tail clinical physical examination, weight audit, ear/eye hygiene check, dental screening, and nutritional plan.",
        "features": ["Physical Vital Stats", "Heart & Lung Auscultation", "Dental & Skin Audit"],
    },
    {
        "id": "srv-2",
        "name": "Core Dog Vaccination Bundle (7-in-1)",
        "category": "dogs",
        "categoryLabel": "For Dogs 🐶",
        "price": "₹1,499 / $45",
        "image": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee?auto=format&fit=crop&w=600&q=80",
        "description": "Protection against Rabies, DHPP, Parvovirus, Distemper, and Hepatitis. Includes digital vaccination passport updates.",
        "features": ["DHPPi + Rabies Shield", "Deworming Dose Included", "Digital Health Record"],
    },
    {
        "id": "srv-3",
        "name": "Canine Ultrasound Dental Scaling & Polish",
        "category": "dogs",
        "categoryLabel": "For Dogs 🐶",
        "price": "₹2,499 / $75",
        "image": "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?auto=format&fit=crop&w=600&q=80",
        "description": "Removal of stubborn tartar and plaque under mild sedation using ultrasonic scaling, followed by fluoride polishing.",
        "features": ["Ultrasonic Scale", "Subgingival Polish", "Fresh Breath Treatment"],
    },
    {
        "id": "srv-4",
        "name": "Feline Comprehensive Wellness & Blood Panel",
        "category": "cats",
        "categoryLabel": "For Cats 🐱",
        "price": "₹1,299 / $40",
        "image": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=600&q=80",
        "description": "Stress-free exam designed specifically for cats. Complete Blood Count (CBC), kidney marker screening, and thyroid assessment.",
        "features": ["CBC & Biochemistry", "Stress-Free Handling", "Renal Health Check"],
    },
    {
        "id": "srv-5",
        "name": "Cat Triple Vaccine & Deworming Protocol",
        "category": "cats",
        "categoryLabel": "For Cats 🐱",
        "price": "₹1,399 / $42",
        "image": "https://images.unsplash.com/photo-1573865526739-10659fec78a5?auto=format&fit=crop&w=600&q=80",
        "description": "Feline Viral Rhinotracheitis, Calicivirus, Panleukopenia (FVRCP) + Anti-Rabies vaccination with broad-spectrum deworming.",
        "features": ["FVRCP + Rabies Shield", "Internal Parasite Control", "Gentle Administration"],
    },
    {
        "id": "srv-6",
        "name": "Feline De-matting & Spa Grooming Package",
        "category": "cats",
        "categoryLabel": "For Cats 🐱",
        "price": "₹1,899 / $55",
        "image": "https://images.unsplash.com/photo-1561948955-570b270e7c36?auto=format&fit=crop&w=600&q=80",
        "description": "Gentle coat de-shedding, nail clipping, sanitary trim, hypoallergenic warm bath, and ear cleaning for short & long-haired breeds.",
        "features": ["Coat De-shedding", "Nail Trimming", "Ear Hygiene Spa"],
    },
    {
        "id": "srv-7",
        "name": "Avian & Bird Health Consultation",
        "category": "all_animals",
        "categoryLabel": "All Animals 🦜",
        "price": "₹899 / $28",
        "image": "https://images.unsplash.com/photo-1552728089-57bdde30beb3?auto=format&fit=crop&w=600&q=80",
        "description": "Beak and feather physical analysis, crop swab analysis, nutritional guidance, and wing/beak trimming for all parrot species & songbirds.",
        "features": ["Feather & Beak Inspection", "Crop Swab Test", "Nutrition Blueprint"],
    },
    {
        "id": "srv-8",
        "name": "Exotic Mammal Exam (Rabbits, Hamsters, Guinea Pigs)",
        "category": "all_animals",
        "categoryLabel": "All Animals 🐇",
        "price": "₹799 / $25",
        "image": "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?auto=format&fit=crop&w=600&q=80",
        "description": "Specialized dental occlusion check, GI stasis screening, parasite check, and diet consultation for small exotic pocket pets.",
        "features": ["Dental Occlusion Check", "GI Stasis Screen", "Parasite Prevention"],
    },
    {
        "id": "srv-9",
        "name": "24/7 Emergency Trauma & Critical ICU Care",
        "category": "all_animals",
        "categoryLabel": "All Animals 🚨",
        "price": "₹2,999 / $90",
        "image": "https://images.unsplash.com/photo-1576201836106-db1758fd1c97?auto=format&fit=crop&w=600&q=80",
        "description": "Immediate stabilization for toxic ingestions, vehicle accidents, breathing distress, and acute pain with oxygen cage therapy.",
        "features": ["Immediate Vet Triage", "Oxygen & IV Fluids", "24/7 Vital Monitoring"],
    },
    {
        "id": "srv-10",
        "name": "Soft Tissue & Orthopedic Surgery Consultation",
        "category": "all_animals",
        "categoryLabel": "All Animals 🩺",
        "price": "₹1,999 / $60",
        "image": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=600&q=80",
        "description": "Pre-surgical digital X-ray evaluation, spay/neuter counseling, fracture plating assessment, and lump biopsy.",
        "features": ["Digital X-Ray Review", "Anesthesia Risk Audit", "Surgical Planning"],
    },
    {
        "id": "srv-11",
        "name": "Microchipping & International Health Passport",
        "category": "all_animals",
        "categoryLabel": "All Animals 🐾",
        "price": "₹1,199 / $35",
        "image": "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?auto=format&fit=crop&w=600&q=80",
        "description": "ISO-compliant RFID microchip implantation with lifetime global database registry and travel health clearance documentation.",
        "features": ["ISO 11784 Microchip", "Lifetime Registry", "Travel Certificate"],
    },
    {
        "id": "srv-12",
        "name": "Pet Allergy & Dermatology Allergy Testing",
        "category": "dogs",
        "categoryLabel": "For Dogs & Cats 🐶🐱",
        "price": "₹1,599 / $48",
        "image": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=600&q=80",
        "description": "Cytology skin scrape, fungal culture, and food allergy elimination trial for pets suffering from chronic itching and hair loss.",
        "features": ["Skin Cytology Scrape", "Fungal & Bacterial Culture", "Custom Diet Plan"],
    },
]


def load_public_page() -> str:
    html_path = os.path.join(os.path.dirname(__file__), "prasanna clinic.html")
    with open(html_path, "r", encoding="utf-8") as handle:
        html = handle.read()

    settings = get_owner_settings()
    replacements = {
        "{{clinic_name}}": settings.get("clinic_name", "Prasanna Pet Care Clinic"),
        "{{clinic_logo}}": settings.get("clinic_logo", ""),
        "{{home_banner}}": settings.get("home_banner", ""),
        "{{dashboard_banner}}": settings.get("dashboard_banner", ""),
        "{{contact_number}}": settings.get("contact_number", "+91 9342301937"),
        "{{email_address}}": settings.get("email_address", "clinic@prasannapetcare.com"),
        "{{clinic_address}}": settings.get("clinic_address", "#62 SNS College Coimbatore"),
        "{{opening_hours}}": settings.get("opening_hours", "24/7 Emergency Care"),
        "{{theme_color}}": settings.get("theme_color", "#10b981"),
        "{{announcement_banner}}": settings.get("announcement_banner", ""),
        "{{home_images}}": settings.get("home_images", ""),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


@app.before_request
def initialize_database() -> None:
    init_db()


@app.route("/")
def home() -> str:
    return load_public_page()


@app.route("/appointment")
def appointment_page() -> str:
    return load_public_page()


@app.route("/appointment/booking")
def appointment_booking_page():
    return load_public_page()


@app.route("/my-appointments")
def my_appointments_page():
    token_number = request.args.get("token", "")
    mobile = request.args.get("mobile", "")
    appointments: list[dict[str, Any]] = []

    if token_number:
        appointment = get_appointment_by_token(token_number)
        if appointment:
            appointments = [appointment]
    elif mobile:
        appointments = get_appointments({"search": mobile})

    appointments = sorted(
        appointments,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return render_template(
        "my_appointments.html",
        appointments=appointments,
        appointment=appointments[0] if appointments else None,
        token_number=token_number,
        mobile=mobile,
    )


@app.route("/appointment-history")
def appointment_history_page():
    token_number = request.args.get("token", "")
    mobile = request.args.get("mobile", "")
    appointments: list[dict[str, Any]] = []

    if token_number:
        appointment = get_appointment_by_token(token_number)
        if appointment:
            appointments = [appointment]
    elif mobile:
        appointments = get_appointments({"search": mobile})

    appointments = sorted(
        appointments,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    return render_template(
        "appointment_history.html",
        appointments=appointments,
        token_number=token_number,
        mobile=mobile,
    )


@app.route("/appointment/success")
def appointment_success_page():
    token_number = request.args.get("token", "")
    appointment = get_appointment_by_token(token_number) if token_number else None
    return render_template("appointment_success.html", appointment=appointment)


@app.route("/services")
def services_page() -> str:
    return load_public_page()


@app.route("/about")
def about_page() -> str:
    return load_public_page()


@app.route("/contact")
def contact_page() -> str:
    return load_public_page()


@app.route("/admin")
def admin_root():
    return redirect("/admin/login")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        error = "Invalid admin credentials."
    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    stats = get_dashboard_stats()
    settings = get_owner_settings()
    return render_template("admin_dashboard.html", stats=stats, settings=settings)


@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    settings = get_owner_settings()
    if request.method == "POST":
        updated_settings = save_owner_settings(request.form.to_dict())
        settings = updated_settings
        return redirect("/admin/settings")

    return render_template("admin_settings.html", settings=settings)


@app.route("/admin/appointments")
def admin_appointments():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    filters = {
        "search": request.args.get("search", ""),
        "status": request.args.get("status", ""),
        "date_filter": request.args.get("date_filter", ""),
    }
    appointments = get_appointments(filters)
    return render_template("admin_appointments.html", appointments=appointments)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")


@app.route("/api/services", methods=["GET"])
def get_services():
    return jsonify({"status": "success", "count": len(SERVICES_CATALOG), "data": SERVICES_CATALOG})


@app.route("/api/book", methods=["POST"])
def handle_booking_api():
    data = request.form.to_dict() if request.form else {}
    if not data and request.is_json:
        data = request.get_json(silent=True) or {}

    try:
        appointment = create_appointment(data)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    return jsonify({"success": True, "token_number": appointment["token_number"], "status": "Pending", "redirect_url": f"/appointment/success?token={appointment['token_number']}"})


@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    filters = {
        "search": request.args.get("search", ""),
        "status": request.args.get("status", ""),
        "date_filter": request.args.get("date_filter", ""),
    }
    return jsonify(get_appointments(filters))


@app.route("/api/update", methods=["POST"])
def update_route():
    appointment_id = request.form.get("appointment_id") or request.args.get("appointment_id")
    if not appointment_id:
        return jsonify({"success": False, "error": "appointment_id is required"}), 400

    updates: dict[str, Any] = {}
    for field in ["owner_name", "mobile", "email", "pet_name", "pet_type", "breed", "age", "gender", "weight", "service", "appointment_date", "appointment_time", "symptoms", "status"]:
        if field in request.form:
            updates[field] = request.form[field]

    appointment = update_appointment(int(appointment_id), updates)
    return jsonify({"success": True, "appointment": appointment})


@app.route("/api/delete", methods=["POST"])
def delete_route():
    appointment_id = request.form.get("appointment_id") or request.args.get("appointment_id")
    if not appointment_id:
        return jsonify({"success": False, "error": "appointment_id is required"}), 400
    deleted = delete_appointment(int(appointment_id))
    return jsonify({"success": deleted})


@app.route("/api/status", methods=["GET"])
def status_route():
    token_number = request.args.get("token") or request.args.get("token_number")
    appointment_id = request.args.get("id")
    if token_number:
        appointment = get_appointment_by_token(token_number)
    elif appointment_id:
        appointment = get_appointment_by_id(int(appointment_id))
    else:
        appointment = None
    if not appointment:
        return jsonify({"success": False, "error": "appointment not found"}), 404
    return jsonify({"success": True, "appointment": appointment})


if __name__ == "__main__":
    print("=" * 60)
    print("🐾 Prasanna Pet Care Clinic - Appointment Management System 🐾")
    print("Serving on: http://127.0.0.1:5000")
    print("LAN access: use your PC IP address on the same Wi-Fi, for example http://192.168.1.x:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)

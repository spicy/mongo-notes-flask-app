import os
from datetime import UTC, datetime

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_pymongo import PyMongo

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config["MONGO_URI"] = os.getenv(
    "MONGODB_URI", "mongodb://localhost:27017/mongo-notes-flask-app"
)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")

# Initialize PyMongo
mongo = PyMongo(app)


# Input validation
def validate_note_input(cwid, full_name, content):
    errors = []
    if not cwid or not cwid.strip():
        errors.append("CWID is required")
    if not full_name or not full_name.strip():
        errors.append("Full name is required")
    if not content or not content.strip():
        errors.append("Note content is required")
    if not cwid.isdigit():
        errors.append("CWID must contain only numbers")
    if len(cwid) != 9:
        errors.append("CWID must be 9 digits")
    return errors


@app.route("/")
def home():
    try:
        notes = mongo.db.notes.find().sort("created_at", -1)
        return render_template("home.html", notes=notes)
    except Exception as e:
        app.logger.error(f"Error retrieving notes: {str(e)}")
        flash("Unable to retrieve notes. Please try again later.", "error")
        return render_template("home.html", notes=[])


@app.route("/add", methods=["POST"])
def add_note():
    try:
        cwid = request.form.get("cwid")
        full_name = request.form.get("full_name")
        content = request.form.get("content")

        # Validate input
        errors = validate_note_input(cwid, full_name, content)
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("home"))

        note_data = {
            "cwid": cwid,
            "full_name": full_name.strip(),
            "content": content.strip(),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mongo.db.notes.insert_one(note_data)
        flash("Note added successfully!", "success")

    except Exception as e:
        app.logger.error(f"Error adding note: {str(e)}")
        flash("Unable to add note. Please try again later.", "error")

    return redirect(url_for("home"))


@app.route("/delete/<note_id>")
def delete_note(note_id):
    try:
        if not ObjectId.is_valid(note_id):
            flash("Invalid note ID", "error")
            return redirect(url_for("home"))

        result = mongo.db.notes.delete_one({"_id": ObjectId(note_id)})

        if result.deleted_count > 0:
            flash("Note deleted successfully!", "success")
        else:
            flash("Note not found!", "error")

    except Exception as e:
        app.logger.error(f"Error deleting note: {str(e)}")
        flash("Unable to delete note. Please try again later.", "error")

    return redirect(url_for("home"))


# API endpoints for potential future use
@app.route("/api/notes", methods=["GET"])
def get_notes():
    try:
        notes = list(mongo.db.notes.find().sort("created_at", -1))
        for note in notes:
            note["_id"] = str(note["_id"])
        return jsonify({"notes": notes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")

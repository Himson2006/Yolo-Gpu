import os, json
from flask import (
    Blueprint, request, current_app,
    render_template, redirect, url_for, send_from_directory, jsonify
)
from sqlalchemy import cast, Integer
from app import db
from app.models import Video, Detection

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("main.search_videos"))

@main_bp.route("/search", methods=["GET"])
def search_videos():
    class_name = request.args.get("class_name", type=str)
    min_count  = request.args.get("min_count",  type=int)
    videos     = []

    if class_name:
        q = Video.query.join(Detection)
        q = q.filter(Detection.classes_detected.ilike(f"%{class_name}%"))

        if min_count is not None:
            # JSONB field access → filter by the integer value stored under that key
            q = q.filter(
                cast(Detection.max_count_per_frame[class_name], Integer) >= min_count
            )

        videos = q.all()
        current_app.logger.info(
            f"[search] Found {len(videos)} videos for '{class_name}' min_count={min_count}"
        )

    return render_template(
        "search.html",
        videos=videos,
        class_name=class_name,
        min_count=min_count
    )

@main_bp.route("/videos", methods=["GET"])
def list_videos():
    class_name = request.args.get("class_name", type=str)
    min_count  = request.args.get("min_count",  type=int)
    q = Video.query.join(Detection)

    if class_name:
        q = q.filter(Detection.classes_detected.ilike(f"%{class_name}%"))
        if min_count is not None:
            q = q.filter(
                cast(Detection.max_count_per_frame[class_name], Integer) >= min_count
            )

    results = [{"id": v.id, "filename": v.filename} for v in q.all()]
    return jsonify(results)

@main_bp.route("/remote_incoming/<int:video_id>", methods=["GET"])
def download_video(video_id: int):
    video = Video.query.get_or_404(video_id)
    # serve out of the incoming/watch folder
    return send_from_directory(
        current_app.config["WATCH_FOLDER"],
        video.filename,
        as_attachment=True
    )

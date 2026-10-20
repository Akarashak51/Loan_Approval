"""
Health-check route.

Used by the frontend on load to verify the Flask API is reachable,
and by developers to confirm the backend started correctly.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify(
        {
            "status": "ok",
            "service": "xai-loan-backend",
            "version": "0.1.0",
        }
    )

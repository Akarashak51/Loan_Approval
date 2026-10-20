from flask import Blueprint, jsonify

from app.middleware.auth_middleware import roles_required
from app.services import ml_service
from app.services.ml_service import MLServiceError

fairness_bp = Blueprint("fairness", __name__)


@fairness_bp.get("/analytics/fairness")
@roles_required("loan_officer", "admin")
def fairness_report():
    try:
        report = ml_service.get_fairness_report()
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify(report), 200

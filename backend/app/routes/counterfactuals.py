from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import roles_required
from app.schemas.application_schema import validate_application_payload
from app.services import ml_service
from app.services.ml_service import MLServiceError

counterfactuals_bp = Blueprint("counterfactuals", __name__)


@counterfactuals_bp.post("/explain/counterfactual")
@roles_required("applicant", "loan_officer", "admin")
def explain_counterfactual():
    data = request.get_json(silent=True) or {}
    errors = validate_application_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    try:
        cf_result = ml_service.get_counterfactual(data)
    except MLServiceError as e:
        return jsonify({"error": e.message}), e.status_code

    # If counterfactual generation fails, callers should still be able to
    # show the prediction + other explanations (spec section 38) --
    # this endpoint just reports found=False rather than erroring.
    return jsonify(cf_result), 200

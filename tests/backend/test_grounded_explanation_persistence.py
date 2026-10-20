from app.extensions import db
from app.models import Applicant, Application, Explanation, GroundedExplanation, Prediction, User
from app.services import ml_service


def test_persisted_application_explanation_is_reused(client, app, monkeypatch):
    with app.app_context():
        user = User(email="grounded@example.com", full_name="Grounded Test", role="applicant")
        user.set_password("strong-password-123")
        db.session.add(user)
        db.session.flush()
        applicant = Applicant(user_id=user.id, full_name=user.full_name)
        db.session.add(applicant)
        db.session.flush()
        application = Application(applicant_id=applicant.id, features_json="{}")
        db.session.add(application)
        db.session.flush()
        prediction = Prediction(application_id=application.id, decision="REVIEW", probability=0.4, model_name="test")
        db.session.add(prediction)
        db.session.flush()
        shap = Explanation(prediction_id=prediction.id, method="shap", plain_english="raw")
        shap.set_contributions([{"feature": "income", "contribution": 0.2}])
        db.session.add(shap)
        db.session.commit()
        user_id, application_id = user.id, application.id

    calls = {"count": 0}

    def fake_explain(_drivers):
        calls["count"] += 1
        return {"text": "income matters", "source": "template", "grounded_in": ["income"]}

    with app.app_context():
        user = User.query.get(user_id)
        monkeypatch.setattr("explain.grounded_explanation.explain", fake_explain)
        first = ml_service.get_grounded_application_explanation(application_id, user)
        second = ml_service.get_grounded_application_explanation(application_id, user)
        assert GroundedExplanation.query.filter_by(application_id=application_id).count() == 1
    assert first["text"] == second["text"] == "income matters"
    assert calls["count"] == 1
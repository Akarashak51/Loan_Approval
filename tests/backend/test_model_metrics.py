from app.extensions import db
from app.models import ModelMetric
from app.services import ml_service


def test_model_metrics_endpoint_persists_both_snapshots(client, app):
    result = ml_service.get_models_metrics()

    assert set(result["latest"]) == {"income_model", "transaction_model"}
    assert all({"precision", "recall", "f1", "roc_auc"}.issubset(metric) for metric in result["latest"].values())
    with app.app_context():
        assert db.session.query(ModelMetric).count() == 2
        assert {metric.model_key for metric in ModelMetric.query.all()} == {"income_model", "transaction_model"}
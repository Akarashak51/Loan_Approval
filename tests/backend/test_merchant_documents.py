from app.extensions import db
from app.models import MerchantTransactionProfile


def _token(client):
    response = client.post("/api/auth/register", json={
        "full_name": "Merchant Test", "email": "merchant-doc@example.com", "password": "strong-password-123",
    })
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


def test_document_verification_is_persisted_and_retrievable(client, app):
    with app.app_context():
        db.session.add(MerchantTransactionProfile(
            merchant_id="merchant-known", gmv_trend_30d=0, gmv_trend_90d=0,
            payment_success_rate=0.95, refund_rate=0.04, chargeback_rate=0.01,
            customer_concentration=0.2, order_volume_volatility=0.4, account_age_days=365,
            actual_monthly_gmv=100000, actual_monthly_inflow=80000,
        ))
        db.session.commit()

    headers = _token(client)
    payload = {
        "gst_reported_monthly_revenue": 65000,
        "bank_statement_avg_balance": 50000,
        "bank_statement_monthly_inflow": 80000,
    }
    response = client.post("/api/merchants/merchant-known/verify-documents", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.get_json()["consistent"] is False
    assert response.get_json()["mismatches"][0]["discrepancy_pct"] == 35.0
    retrieved = client.get("/api/merchants/merchant-known/verify-documents", headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.get_json()["gst_reported_monthly_revenue"] == 65000
    assert retrieved.get_json()["consistent"] is False
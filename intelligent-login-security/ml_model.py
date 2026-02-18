from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from models import LoginHistory, db

# Simple in-memory model cache (per user)
_model_cache = {}


def _get_user_history_features(user_id: int) -> pd.DataFrame:
    """
    Return a DataFrame of numeric features for a user's login history.
    Columns: login_hour, ip_encoded, device_encoded
    """
    records: List[LoginHistory] = (
        LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.timestamp.asc()).all()
    )
    if not records:
        return pd.DataFrame(columns=["login_hour", "ip_encoded", "device_encoded"])

    data = {
        "login_hour": [r.login_hour for r in records],
        "ip_encoded": [r.ip_encoded for r in records],
        "device_encoded": [r.device_encoded for r in records],
    }
    return pd.DataFrame(data)


def train_model(user_id: int) -> Optional[IsolationForest]:
    """
    Train an IsolationForest model for the specified user based on their login history.
    If user has less than 10 logins, returns None (no model).
    """
    df = _get_user_history_features(user_id)
    if df.shape[0] < 10:
        _model_cache.pop(user_id, None)
        return None

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )
    model.fit(df.values)
    _model_cache[user_id] = model
    return model


def predict_anomaly(user_id: int, login_features: List[float]) -> bool:
    """
    Predict whether the given login_features are anomalous for this user.

    login_features: [login_hour, ip_encoded, device_encoded]
    Returns True if suspicious, False otherwise or if model not available.
    """
    # Ensure the latest data is used; retrain on demand
    df = _get_user_history_features(user_id)
    if df.shape[0] < 10:
        return False  # skip anomaly detection when insufficient data

    model = _model_cache.get(user_id)
    if model is None:
        model = train_model(user_id)

    if model is None:
        return False

    arr = np.array(login_features, dtype=float).reshape(1, -1)
    prediction = model.predict(arr)[0]  # -1 = anomaly, 1 = normal
    return prediction == -1
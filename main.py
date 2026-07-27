import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import firestore
import bigquery_service

app = FastAPI()
db = firestore.Client()

# --- Pydantic Schemas ---

class UserPayload(BaseModel):
    name: str
    email: str
    role: Optional[str] = "user"

class TelemetryPayload(BaseModel):
    device_id: str
    event_type: str
    timestamp: str
    metadata: Optional[dict] = None

class BatchTelemetryPayload(BaseModel):
    events: List[TelemetryPayload]

class AlertPayload(BaseModel):
    severity: str
    message: str
    details: Optional[dict] = None


# --- 1. Root & System Health Probes ---

@app.get("/")
def read_root():
    return {"status": "online", "message": "Serverless API Gateway operational"}

@app.get("/health/liveness")
def health_liveness():
    return {"status": "alive"}

@app.get("/health/readiness")
def health_readiness():
    try:
        db.collection("health").document("ping").get()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unready: {str(e)}")


# --- 2. User Management (Complete Firestore CRUD) ---

@app.post("/api/users/{user_id}")
def create_user(user_id: str, user: UserPayload):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc_ref.set(user.model_dump())
        return {"status": "success", "user_id": user_id, "data": user.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    try:
        doc_ref = db.collection("users").document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "success", "user_id": user_id, "data": doc.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}")
def update_user(user_id: str, user: UserPayload):
    try:
        doc_ref = db.collection("users").document(user_id)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="User not found")
        doc_ref.update(user.model_dump())
        return {"status": "success", "message": f"User {user_id} updated."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}")
def delete_user(user_id: str):
    try:
        doc_ref = db.collection("users").document(user_id)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="User not found")
        doc_ref.delete()
        return {"status": "success", "message": f"User {user_id} deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 3. Telemetry Event Ingestion ---

@app.post("/telemetry")
def ingest_telemetry(payload: TelemetryPayload):
    return {"status": "success", "received": payload.model_dump()}

@app.post("/telemetry/batch")
def ingest_batch_telemetry(payload: BatchTelemetryPayload):
    count = len(payload.events)
    return {"status": "success", "processed_count": count}


# --- 4. Analytics Engine (BigQuery) ---

@app.get("/analytics/device-breakdown")
def get_analytics():
    try:
        results = bigquery_service.get_device_breakdown()
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. AI Agent Operational Alerting ---

@app.post("/api/system_alert")
def receive_system_alert(alert: AlertPayload):
    try:
        doc_ref = db.collection("system_alerts").document()
        doc_ref.set(alert.model_dump())
        return {"status": "success", "message": "Alert logged successfully to Firestore."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
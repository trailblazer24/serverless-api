from fastapi import FastAPI, HTTPException
from bigquery_service import BigQueryService
from google.cloud import firestore
from pydantic import BaseModel

app = FastAPI()
bq_service = BigQueryService()

# Initialize the Firestore client
# When deployed to Cloud Run, it automatically detects your project ID and credentials
db = firestore.Client()

# Define what a data payload should look like
class UserPayload(BaseModel):
    name: str
    email: str
    role: str

class TelemetryPayload(BaseModel):
    user_id: str
    device: str
    event_type: str

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "API Gateway is running live!"}

# Endpoint 1: Save data to Firestore
@app.post("/api/users/{user_id}")
def create_user(user_id: str, user: UserPayload):
    try:
        # Reference a collection named 'users' and a document named after the user_id
        doc_ref = db.collection("users").document(user_id)
        
        # Save the data payload as a dictionary
        doc_ref.set(user.model_dump())
        
        return {"status": "success", "message": f"User {user_id} saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2: Fetch data from Firestore
@app.get("/api/users/{user_id}")
def get_user(user_id: str):
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        raise HTTPException(status_code=404, detail="User not found in database")
    
@app.get("/analytics/device-breakdown")
def read_device_breakdown():
    """
    Fetches real-time telemetry metrics directly from BigQuery.
    """
    data = bq_service.get_device_breakdown()
    if not data:
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics from BigQuery.")
    return {"status": "success", "data": data}

@app.post("/telemetry")
def ingest_telemetry(payload: TelemetryPayload):
    """
    Ingests event telemetry from clients/simulators.
    """
    return {"status": "success", "received": payload.model_dump()}
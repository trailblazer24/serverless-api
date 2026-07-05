from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "API Gateway is running!"}

@app.get("/api/data")
def get_mock_data():
    return {
        "user_id": 1, 
        "event": "login", 
        "location": "Niagara"
    }
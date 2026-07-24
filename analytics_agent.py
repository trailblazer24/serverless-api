import os
import json
import time
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from google.cloud import bigquery

load_dotenv()  # Load environment variables from .env file

# ==========================================
# 1. Configuration & Client Initializations
# ==========================================

bq_client = bigquery.Client()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_GATEWAY_URL = os.getenv(
    "API_GATEWAY_URL", 
    "https://serverless-api-1064504272560.northamerica-northeast1.run.app"
)

if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY environment variable is missing. Set it before running.")

ai_client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================
# 2. Tool Definitions
# ==========================================

def run_bigquery_sql(sql_query: str) -> str:
    """Executes a read-only SQL query against the BigQuery telemetry database and returns JSON results."""
    print(f"\n[Tool Execution] 📊 Executing BigQuery SQL:\n{sql_query}\n")
    try:
        query_job = bq_client.query(sql_query)
        results = [dict(row) for row in query_job.result()]
        return json.dumps(results, default=str)
    except Exception as e:
        error_msg = f"Error executing BigQuery query: {str(e)}"
        print(f"⚠️ {error_msg}")
        return json.dumps({"error": error_msg})


def send_gateway_alert(anomaly_type: str, severity: str, details: str) -> str:
    """Sends an automated POST system notification back to the FastAPI API Gateway."""
    endpoint = f"{API_GATEWAY_URL.rstrip('/')}/api/users/system_alert"
    print(f"\n[Tool Execution] 🚨 Triggering API Gateway Webhook Alert at: {endpoint}")
    
    payload = {
        "name": f"ALERT_{anomaly_type.upper().replace(' ', '_')}",
        "email": f"severity_{severity.lower()}@agent.internal",
        "role": f"System Alert: {details[:80]}"
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        print(f"✅ Gateway Webhook Status Code: {response.status_code}")
        return json.dumps({
            "status_code": response.status_code,
            "response": response.json() if response.ok else response.text
        })
    except Exception as e:
        error_msg = f"Failed to reach API Gateway: {str(e)}"
        print(f"⚠️ {error_msg}")
        return json.dumps({"error": error_msg})



# Helper function using active gemini-3.6-flash with retry backing
def safe_generate_content(contents, config, model="gemini-3.6-flash", retries=3):
    for attempt in range(retries):
        try:
            return ai_client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except ClientError as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = 12 * (attempt + 1)
                print(f"⏳ Rate limit hit. Pausing for {wait_time}s before retrying...")
                time.sleep(wait_time)
            else:
                raise e


# ==========================================
# 3. Main Agent Loop (Multi-Turn Resilient)
# ==========================================

def run_agent_audit():
    print("🤖 AI Agent initializing operational audit loop...")

    system_instruction = """
    You are an Autonomous System Operations & Telemetry Inspector for an enterprise data platform.
    
    Database Target: `flash-gasket-486800-p9.telemetry_data.telemetry_events_optimized`
    Table Schema:
      - timestamp (TIMESTAMP)
      - user_id (STRING)
      - session_id (STRING)
      - event_type (STRING)
      - device_type (STRING)
      - coordinate_x (FLOAT)
      - coordinate_y (FLOAT)
      - coordinate_z (FLOAT)

    Workflow:
    1. Query BigQuery to inspect incoming event counts, event types, and check for high-frequency critical errors (`system_crash_critical`) or suspicious coordinate anomalies.
    2. If you detect critical failure patterns or spikes, call `send_gateway_alert`.
    3. Return a concise summary of your findings and actions taken.
    """

    user_prompt = "Audit recent telemetry events in BigQuery, check for any critical error or system crash anomalies, and trigger an alert to the API Gateway if issues are detected."

    tools = [run_bigquery_sql, send_gateway_alert]
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        temperature=0.1,
    )

    # Maintain conversation state for tool loops
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])]

    max_turns = 5
    for turn in range(max_turns):
        response = safe_generate_content(
            contents=contents,
            config=config,
            model="gemini-3.6-flash"
        )
        
        # Append assistant's thoughts/tool requests to conversation history
        contents.append(response.candidates[0].content)

        if not response.function_calls:
            print("\n📝 Agent Final Audit Summary:")
            print(response.text)
            break

        # Process function calls returned by model
        tool_responses = []
        for call in response.function_calls:
            print(f"🛠️ Agent called tool: {call.name}")
            print(f"📥 Arguments: {call.args}")
            
            tool_result = ""
            if call.name == "run_bigquery_sql":
                tool_result = run_bigquery_sql(**call.args)
            elif call.name == "send_gateway_alert":
                tool_result = send_gateway_alert(**call.args)

            tool_responses.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": tool_result}
                )
            )

        # Pass tool results back to model
        contents.append(types.Content(role="tool", parts=tool_responses))


if __name__ == "__main__":
    run_agent_audit()
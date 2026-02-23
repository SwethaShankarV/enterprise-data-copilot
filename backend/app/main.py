from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import json
import logging
logging.basicConfig(level=logging.INFO)

from app.config import OPENAI_API_KEY, MODEL_NAME
from app.tools.sql_adapter import run_sql_query

app = FastAPI()
sessions = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # dev + Docker frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

class Query(BaseModel):
    message: str

# @app.post("/chat")
# def chat(query: Query, session_id: str = "default"):

#     if session_id not in sessions:
#         sessions[session_id] = [
#             {
#                 "role": "system",
#                 "content": """
#                 You are an enterprise data assistant.
#                 The database has a table named 'sales' with columns:
#                 id, region, product, revenue, order_date.
#                 Use SQL when needed.
#                 """
#             }
#         ]

#     sessions[session_id].append(
#         {"role": "user", "content": query.message}
#     )

#     tools = [
#         {
#             "type": "function",
#             "function": {
#                 "name": "run_sql_query",
#                 "description": "Run a SQL query on the enterprise sales database.",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "query": {
#                             "type": "string",
#                             "description": "SQL query to execute"
#                         }
#                     },
#                     "required": ["query"]
#                 }
#             }
#         }
#     ]

#     response = client.chat.completions.create(
#         model=MODEL_NAME,
#         messages=sessions[session_id],
#         tools=tools,
#         tool_choice="auto"
#     )

#     message = response.choices[0].message

#     if message.tool_calls:
#         tool_call = message.tool_calls[0]
#         arguments = json.loads(tool_call.function.arguments)

#         result = run_sql_query(arguments["query"])

#         sessions[session_id].append(message)
#         sessions[session_id].append({
#             "role": "tool",
#             "tool_call_id": tool_call.id,
#             "content": json.dumps(result)
#         })

#         second_response = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=sessions[session_id]
#         )

#         final_message = second_response.choices[0].message
#         sessions[session_id].append(final_message)

#         # Build chart payload when result is a 2-column aggregate (labels + values) 
#         # Example: if result has columns ["product","revenue"]
#         if "columns" in result and len(result["columns"]) == 2 and "rows" in result:
#             chart = {
#                 "labels": [row[0] for row in result["rows"]],
#                 "values": [row[1] for row in result["rows"]],
#                 "label": result["columns"][1]
#             }
#         else:
#             chart = None

#         return {"response": final_message.content, "chart": chart}
#         # return {"response": final_message.content}

#     sessions[session_id].append(message)

#     return {"response": message.content}

from app.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()

@app.post("/chat")
def chat(query: Query, session_id: str = "default"):

    if session_id not in sessions:
        sessions[session_id] = [
            {
                "role": "system",
                "content": "You are an enterprise data assistant. The only table is \"sales\" with exactly these columns: id (INTEGER), region (TEXT), product (TEXT), revenue (FLOAT), order_date (TEXT). Use these exact column names in SQL (e.g. \"product\", not \"product_line\" or \"product_name\"). Use SQL when needed."
            }
        ]

    sessions[session_id].append({"role": "user", "content": query.message})

    response_text, structured = orchestrator.route(sessions[session_id])
    chart = None

    # structured is expected to be {'columns': [...], 'rows': [[...], ...]} or None
    if structured and isinstance(structured, dict) and "columns" in structured:
        cols = structured["columns"]
        rows = structured["rows"]
        # If it's a two-column aggregated result (label,value)
        if len(cols) >= 2 and len(rows) > 0:
            chart = {
                "labels": [row[0] for row in rows],
                "values": [row[1] for row in rows],
                "label": cols[1]
            }

    sessions[session_id].append({"role":"assistant","content":response_text})
    return {"response": response_text, "chart": chart}
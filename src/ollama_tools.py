# src/ollama_tools.py
import json

# Define a list of callable tools for the model
TOOLS = [
    {
        "type": "function",
        "name": "get_appointment_lists",
        "description": "Get List of appointments for next days",
        # "parameters": {
        #     "type": "object",
        #     "properties": {
        #         "sign": {
        #             "type": "string",
        #             "description": "An astrological sign like Taurus or Aquarius",
        #         },
        #     },
        #     "required": ["sign"],
        # },
    },
]
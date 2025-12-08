# src/ollama_tools.py
import json

# Define a list of callable tools for the model
TOOLS = [
    {
        "type": "function",
        "name": "get_appointment_lists",
        "description": "Get List of appointments for next days",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Start datetime (inclusive) in ISO 8601, e.g. 2025-12-07T14:00:00Z. Optional."
                },
                "end": {
                    "type": "string",
                    "format": "date-time",
                    "description": "End datetime (inclusive) in ISO 8601. Optional."
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Max number of appointments to return. Optional (default 48)."
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_occupied_slots",
        "description": "Check for occupied time slots based on given criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Start datetime (inclusive) in ISO 8601, e.g. 2025-12-07T14:00:00Z."
                },
                "end": {
                    "type": "string",
                    "format": "date-time",
                    "description": "End datetime (inclusive) in ISO 8601."
                }
            },
            "required": ["start", "end"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "save_appointment",
        "description": "Save appointment on database",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the person booking the appointment."
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email address (optional)."
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number (optional)."
                },
                "date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Appointment datetime in ISO 8601, e.g. 2025-12-07T14:00:00Z."
                },
                "description": {
                    "type": "string",
                    "description": "Short description or notes (optional)."
                }
            },
            "required": ["name", "date"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "update_appointment",
        "description": "Update/modify an existing appointment by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "integer",
                    "description": "ID of the appointment to update."
                },
                "name": {
                    "type": "string",
                    "description": "New full name (optional)."
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "New email (optional)."
                },
                "phone": {
                    "type": "string",
                    "description": "New phone (optional)."
                },
                "date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "New appointment datetime in ISO 8601 (optional)."
                },
                "description": {
                    "type": "string",
                    "description": "New description/notes (optional)."
                }
            },
            "required": ["appointment_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "delete_appointment",
        "description": "Delete an appointment by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "integer",
                    "description": "ID of the appointment to delete."
                }
            },
            "required": ["appointment_id"],
            "additionalProperties": False,
        },
    },
]
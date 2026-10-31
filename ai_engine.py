import os
import json

from dotenv import load_dotenv
from google import genai


# List of Gemini models to try in order of preference
MODEL_CANDIDATES = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest"
]


# ============================================================
# AI DIAGNOSIS FUNCTION (RESILIENT CLOUD INFERENCE)
# ============================================================

def diagnose(symptom, show_output, topology_context=""):
    """
    Reads .env dynamically and calls Google Gemini API.
    Auto-switches to alternative Gemini Flash models if a model is busy (503) or rate-limited (429).
    """
    load_dotenv(override=True)
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found in .env. Please add your key to .env."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are NetSage AI, an AI-assisted Cisco network troubleshooting assistant.

Your purpose is to help analyze Cisco Packet Tracer troubleshooting cases.

Rules:
- Use the Cisco show-command evidence and network topology context provided.
- Do not invent missing information.
- If evidence is insufficient, clearly say so.
- Give a likely diagnosis, not absolute certainty.
- Recommend the next Cisco command when helpful.
- Ensure all suggested Cisco commands and fix steps strictly align with the exact device names, interface identifiers (e.g., GigabitEthernet0/0/0, FastEthernet0/1), VLAN IDs, and IP addressing schemes provided in the Network Topology & Device Context or Cisco Evidence.
- A human network engineer must review the diagnosis before applying any fix.

Network Symptom:
{symptom}

Network Topology & Device Context:
{topology_context if topology_context.strip() else "Not explicitly specified (infer from evidence if available)"}

Cisco Show Command Output:
{show_output}

Return ONLY valid JSON in exactly this format:

{{
    "root_cause": "",
    "confidence": "",
    "osi_layer": "",
    "evidence": "",
    "next_command": "",
    "fix_steps": []
}}

Requirements:
- confidence must be High, Medium, or Low.
- fix_steps must be a JSON list of specific CLI commands or actionable steps matching the topology.
"""

    response = None
    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                break
        except Exception as err:
            last_error = err
            continue

    if not response or not response.text:
        if last_error:
            raise last_error
        raise RuntimeError("Failed to receive response from Gemini models.")

    text = response.text.strip()

    # Clean markdown formatting if present
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        diagnosis = json.loads(text)
    except json.JSONDecodeError:
        diagnosis = {
            "root_cause": "AI returned an invalid response format.",
            "confidence": "Low",
            "osi_layer": "Unknown",
            "evidence": text,
            "next_command": "Review the Cisco show-command output manually.",
            "fix_steps": [
                "Inspect the Packet Tracer evidence.",
                "Verify the Cisco configuration.",
                "Allow a human reviewer to confirm the diagnosis."
            ]
        }

    return diagnosis
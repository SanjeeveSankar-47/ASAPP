# cancel_agent.py
import os
import sys
import json
import requests

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class CancelTripAgent:
    def __init__(self, api_url: str, api_key: str | None = None):
        self.api_url = api_url.rstrip("/")
        self.cancel_endpoint = f"{self.api_url}/mcp/db/cancel_ticket"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.memory = {}

    def _ask_int(self, prompt: str) -> int:
        while True:
            val = input(prompt).strip()
            if not val:
                print("Please enter a value.")
                continue
            try:
                return int(val)
            except ValueError:
                print("Please enter a numeric id (integer).")

    def run(self):
        print("Agent: Hi! I can help you with your flight cancellation. Let's get started.")
        
        if "user_id" not in self.memory or not self.memory.get("user_id"):
            self.memory["user_id"] = self._ask_int("Agent: Can you please provide your User ID? ")

        if "ticket_id" not in self.memory or not self.memory.get("ticket_id"):
            self.memory["ticket_id"] = self._ask_int("Agent: Great! Now, can you provide your Ticket ID? ")

        payload = {
            "user_id": self.memory["user_id"],
            "ticket_id": self.memory["ticket_id"]
        }

        try:
            resp = requests.post(self.cancel_endpoint, json=payload, headers=self.headers, timeout=10)
        except requests.RequestException as e:
            print("Agent: Network error when calling cancel endpoint:", str(e))
            return {"error": str(e)}

        if resp.status_code >= 200 and resp.status_code < 300:
            try:
                result = resp.json()
            except ValueError:
                print("Agent: Received non-JSON response:", resp.text)
                return {"raw": resp.text}
            print("Agent: Cancellation response:")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Agent: API returned status {resp.status_code}")
            try:
                print(json.dumps(resp.json(), indent=2))
            except ValueError:
                print(resp.text)
            return {"status_code": resp.status_code, "body": resp.text}


if __name__ == "__main__":
    API_BASE = os.getenv("CANCEL_API_BASE", "http://127.0.0.1:8000")
    API_KEY = os.getenv("CANCEL_API_KEY", None)
    cancel_agent = CancelTripAgent(api_url=API_BASE, api_key=API_KEY)
    cancel_agent.run()

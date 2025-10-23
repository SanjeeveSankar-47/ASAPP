import os
import sys

from typing import List
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent import Agent
from config.settings import Settings
from prompts.agent_prompts import INTENT_CLASSIFIER_PROMPT
from groq import Groq


class IntentClassifierAgent:

    def __init__(self):
        self.client = Groq(api_key=Settings().GROQ_API_KEY)
        self.agent = Agent(self.client, INTENT_CLASSIFIER_PROMPT)


    def build_intent_prompt(self, query: str) -> str:
        return INTENT_CLASSIFIER_PROMPT.format(query=query)


    def get_intent(self, query: str) -> List[dict]:
        intent_prompt = self.build_intent_prompt(query)
        response = self.agent(intent_prompt)

        import json
        import re
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                data = json.loads(json_str)
                return data.get("detected_intents", [])
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                return []
        
        print("No JSON found in response")
        return []


if __name__ == "__main__":
    classifier = IntentClassifierAgent()
    intents = classifier.get_intent("i want to cancel my flight from New York to London next Monday.")
    print(intents)
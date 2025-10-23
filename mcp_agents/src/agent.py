import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from groq import Groq



class Agent:
    def __init__(self, client: Groq, system: str = "", tools: list = None):
        self.client = client
        self.system = system
        self.messages = []
        self.tools = tools or []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, messages=""):
        if messages:
            self.messages.append({"role": "user", "content": messages})
        
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=self.messages,
            temperature=0.0,
            tools=self.tools  
        )
        return completion.choices[0].message.content





"""
def agent_loop(max_iterations=20, query: str=""):
    agent = Agent(client, system_prompt)
    tools = ["calculate", "get_planet_mass"]
    next_prompt = query

    i = 0
    while i < max_iterations:
        i += 1
        result = agent(next_prompt)
        print(result)


        if "PAUSE" in result and "Action" in result:
            action = re.findall(r"Action: ([a-z_]+): (.+)", result, re.IGNORECASE)
            chosen_tool = action[0][0]
            arg = action[0][1]
            print(f"tool {chosen_tool} , args {arg}")
            if chosen_tool in tools:
                result_tool = eval(f"{chosen_tool}('{arg}')")
                next_prompt = f"Observation: {result_tool}"

            else:
                next_prompt = "Observation: Tool not found"

            print(next_prompt)
            continue

        if "Answer" in result:
            break


#agent_loop(query="What is the mass of Earth plus the mass of Saturn ")"""
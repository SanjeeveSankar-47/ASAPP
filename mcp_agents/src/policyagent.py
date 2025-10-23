import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp import ClientSession
from mcp_use import MCPAgent, MCPClient
import os
import hashlib
import time
from typing import Dict, Optional

class PolicyAgentManager:
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.agent: Optional[MCPAgent] = None
        self.cache: Dict[str, tuple[str, float]] = {}
        self.cache_ttl = 300 
        self.system_prompt = """You are a helpful travel assistant specializing in flight information, travel policies, and general travel queries. 

Your capabilities include:
- Flight status and information
- Seat availability and booking
- Travel policies (baggage, pets, cancellations, etc.)
- General travel assistance
- Airport information and procedures

Guidelines:
1. Provide clear, concise, and accurate information
2. Use available tools to get real-time information when needed
3. For frequently asked questions, provide comprehensive but efficient responses
4. Be helpful and professional in all interactions
5. If you need to search for information, use the most efficient method available

## KEEP YOUR RESPONSE MORE CONCISE for your final answer.

Perform tasks as efficiently as possible while maintaining accuracy."""
        
    async def initialize(self):
        """Initialize the agent once at startup"""
        if self.client is None:
            load_dotenv()
            os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

            config_file = r"C:\\Users\\jaiak\\Downloads\\new asapp\\NexusAI\\mcp_agents\\src\\browser_mcp.json"

            print("Initializing Policy Agent...")
            
            try:
                self.client = MCPClient.from_config_file(config_file)
                llm = ChatGroq(model="openai/gpt-oss-120b")

                self.agent = MCPAgent(
                    llm=llm,
                    client=self.client,
                    max_steps=15,
                    memory_enabled=True
                )
                
                if hasattr(self.agent, 'messages') or hasattr(self.agent, 'memory'):
                    try:
                        if hasattr(self.agent, 'messages'):
                            self.agent.messages.insert(0, {"role": "system", "content": self.system_prompt})
                        elif hasattr(self.agent, 'memory'):
                            pass
                    except Exception as e:
                        print(f"⚠️ Could not set system message: {e}")
                
                print("✅ Policy Agent initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Policy Agent: {e}")
                raise

    def _get_cache_key(self, user_input: str) -> str:
        """Generate a cache key from user input"""
        normalized_input = user_input.lower().strip()
        return hashlib.md5(normalized_input.encode()).hexdigest()

    def _get_cached_response(self, user_input: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        cache_key = self._get_cache_key(user_input)
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return response
            else:
                del self.cache[cache_key]
        return None

    def _cache_response(self, user_input: str, response: str):
        """Cache the response for future use"""
        cache_key = self._get_cache_key(user_input)
        self.cache[cache_key] = (response, time.time())
        
        if len(self.cache) > 100: 
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

    async def process_query(self, user_input: str) -> str:
        """Process a user query with caching and efficient session management"""
        try:
            cached_response = self._get_cached_response(user_input)
            if cached_response:
                print("✅ Serving from cache")
                return cached_response

            if self.agent is None:
                await self.initialize()

            print(f"🔍 Processing query: {user_input}")
            
            contextualized_query = f"Context: {self.system_prompt}\n\nUser Query: {user_input}"
            
            response = await self.agent.run(contextualized_query)
            
            self._cache_response(user_input, response)
            
            return response

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error while processing your query: {str(e)}"
            print(f"❌ Error in process_query: {e}")
            return error_msg

    async def clear_memory(self):
        """Clear conversation memory while keeping the session alive"""
        if self.agent:
            self.agent.clear_conversation_history()
            print("🗑️ Conversation memory cleared")

    async def close(self):
        """Close the client session"""
        if self.client and self.client.sessions:
            await self.client.close_all_sessions()
            self.client = None
            self.agent = None
            print("🔒 Policy Agent session closed")

policy_agent_manager = PolicyAgentManager()

async def run_memory_chat():
    """Interactive chat mode (for testing)"""
    await policy_agent_manager.initialize()
    
    print("\n==== Interactive MCP chat ====")
    print("Type 'exit' to quit the chat.")
    print("Type 'clear' to clear the memory.")
    print("Type 'cache' to show cache stats.")
    print("=================================\n")

    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            elif user_input.lower() == "clear":
                await policy_agent_manager.clear_memory()
                print("Memory cleared.")
                continue
            elif user_input.lower() == "cache":
                cache_size = len(policy_agent_manager.cache)
                print(f"Cache stats: {cache_size} entries")
                continue
            
            print("\nAssistant: ", end="", flush=True)
            
            try:
                response = await policy_agent_manager.process_query(user_input)
                print(f"Agent: {response}")
            
            except Exception as e:
                print(f"\nError: {e}")

    finally:
        await policy_agent_manager.close()

def process_query_sync(user_input: str) -> str:
    """Synchronous wrapper for Streamlit integration"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if policy_agent_manager.agent is None:
            loop.run_until_complete(policy_agent_manager.initialize())
        
        response = loop.run_until_complete(policy_agent_manager.process_query(user_input))
        loop.close()
        return response
    except Exception as e:
        return f"Error processing your query: {str(e)}"

async def initialize_agent_async():
    """Async initialization for Streamlit"""
    await policy_agent_manager.initialize()

def initialize_agent_sync():
    """Synchronous initialization for Streamlit"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(policy_agent_manager.initialize())
        loop.close()
        print("✅ Policy Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Policy Agent: {e}")

def process_query_simple(user_input: str) -> str:
    """Simple synchronous version without complex initialization"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        load_dotenv()
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        
        config_file = r"C:\\Users\\jaiak\\Downloads\\new asapp\\NexusAI\\mcp_agents\\src\\browser_mcp.json"
        
        client = MCPClient.from_config_file(config_file)
        llm = ChatGroq(model="openai/gpt-oss-120b")
        
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,
            memory_enabled=True,
        )
        
        response = loop.run_until_complete(agent.run(user_input))
        loop.run_until_complete(client.close_all_sessions())
        loop.close()
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    asyncio.run(run_memory_chat())
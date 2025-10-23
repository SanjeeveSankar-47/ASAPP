import streamlit as st
import os
import sys
import asyncio
from policyagent import process_query_sync, initialize_agent_sync

initialize_agent_sync()

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

st.set_page_config(
    page_title="NexusAI Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-response {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ff6b6b;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4f7e2;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #155724;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .warning-message {
        background-color: #fff3cd;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #856404;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-message {
        background-color: #f8d7da;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
        font-size: 1.1rem;
        color: #721c24;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .flow-indicator {
        background-color: #e2e3e5;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-size: 1rem;
        color: #383d41;
        text-align: center;
        font-weight: bold;
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #155a8a;
    }
    .chat-input {
        font-size: 1.1rem;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm NexusAI, your travel assistant. I can help with flight cancellations, status checks, seat availability, and travel policies. How can I assist you today?"}
    ]

if "cancellation_flow" not in st.session_state:
    st.session_state.cancellation_flow = {
        "active": False,
        "step": None, 
        "ticket_id": None,
        "user_id": None
    }

@st.cache_resource
def load_agents():
    try:
        from canceltripagent import CancelTripAgent
        from intentclassifier import IntentClassifierAgent
        
        intent_classifier = IntentClassifierAgent()
        cancel_agent = CancelTripAgent(api_url="http://127.0.0.1:8000")
        
        return {
            "intent_classifier": intent_classifier,
            "cancel_trip": cancel_agent
        }, True
    except ImportError as e:
        return {}, False

agents_dict, agents_loaded = load_agents()

@st.cache_resource
def setup_policy_agent():
    """Setup the PolicyAgent for handling general queries"""
    try:
        from policyagent import run_memory_chat
        return run_memory_chat
    except ImportError:
        return None

policy_agent_func = setup_policy_agent()

async def run_policy_agent_async(user_message: str) -> str:
    """Run policy agent asynchronously and get response"""
    if policy_agent_func is None:
        return "I'm currently unable to process policy-related queries. Please try again later."
    
    try:
        from dotenv import load_dotenv
        from langchain_groq import ChatGroq
        from mcp import ClientSession
        from mcp_use import MCPAgent, MCPClient
        import os
        
        load_dotenv()
        config_file = r"C:\\Users\\jaiak\\Downloads\\new asapp\\NexusAI\\mcp_agents\\src\\browser_mcp.json"
        
        client = MCPClient.from_config_file(config_file)
        llm = ChatGroq(model="openai/gpt-oss-120b")
        
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=15,
            memory_enabled=True,
        )
        
        response = await agent.run(user_message)
        await client.close_all_sessions()
        return response
        
    except Exception as e:
        return f"Policy agent error: {str(e)}"

def run_policy_agent_sync(user_message: str) -> str:
    """Run policy agent synchronously for Streamlit"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(run_policy_agent_async(user_message))
        loop.close()
        return response
    except Exception as e:
        return f"Error processing your query: {str(e)}"

def classify_intent(user_message: str):
    """Classify user intent using IntentClassifierAgent"""
    if not agents_loaded or "intent_classifier" not in agents_dict:
        return []
    
    try:
        intents = agents_dict["intent_classifier"].get_intent(user_message)
        return intents
    except Exception as e:
        return []

def start_cancellation_flow():
    """Start the cancellation flow"""
    st.session_state.cancellation_flow = {
        "active": True,
        "step": "ticket_id",
        "ticket_id": None,
        "user_id": None
    }
    return "🛫 **Flight Cancellation Started**\n\nI can help you cancel your flight. Please provide your **Ticket ID** (any numbers or letters):"

def process_cancellation_flow(user_message: str) -> str:
    """Process messages during cancellation flow"""
    flow = st.session_state.cancellation_flow
    
    if flow["step"] == "ticket_id":
        if user_message.strip():
            ticket_id = user_message.strip()
            st.session_state.cancellation_flow["ticket_id"] = ticket_id
            st.session_state.cancellation_flow["step"] = "user_id"
            return f"✅ **Ticket ID Received**\n\nGot your Ticket ID: **{ticket_id}**\n\nNow please provide your **User ID** (any numbers or letters):"
        else:
            return "❌ **Please provide a Ticket ID**\n\nPlease enter your Ticket ID (it can be any numbers or letters):"
    
    elif flow["step"] == "user_id":
        if user_message.strip():
            user_id = user_message.strip()
            st.session_state.cancellation_flow["user_id"] = user_id
            st.session_state.cancellation_flow["step"] = "confirmation"
            ticket_id = flow["ticket_id"]
            return f"✅ **User ID Received**\n\nGot your User ID: **{user_id}**\n\n**Cancellation Summary:**\n• Ticket ID: {ticket_id}\n• User ID: {user_id}\n\nShould I proceed with cancelling this ticket? Please type **'yes'** to confirm or **'no'** to cancel."
        else:
            return "❌ **Please provide a User ID**\n\nPlease enter your User ID (it can be any numbers or letters):"
    
    elif flow["step"] == "confirmation":
        user_message_lower = user_message.lower().strip()
        if user_message_lower in ['yes', 'y', 'confirm', 'proceed', 'ok']:
            return process_cancellation()
        elif user_message_lower in ['no', 'n', 'cancel', 'stop']:
            return reset_cancellation_flow("❌ **Cancellation Cancelled**\n\nFlight cancellation has been cancelled. How else can I help you?")
        else:
            return "❓ **Confirmation Required**\n\nPlease type **'yes'** to proceed with cancellation or **'no'** to cancel the request:"

def process_cancellation() -> str:
    """Process the actual cancellation"""
    flow = st.session_state.cancellation_flow
    ticket_id = flow["ticket_id"]
    user_id = flow["user_id"]
    
    try:
        if agents_loaded and "cancel_trip" in agents_dict:
            payload = {
                "user_id": user_id,
                "ticket_id": ticket_id
            }
            
            import requests
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/mcp/db/cancel_ticket",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        if "already cancelled" in result.get("message", "").lower():
                            success_msg = f"✅ **Ticket Already Cancelled**\n\n🎫 **Ticket Details:**\n• Ticket ID: {ticket_id}\n• User ID: {user_id}\n\n📝 **Status:** This ticket was already cancelled previously. No further action needed."
                        else:
                            success_msg = f"✅ **Flight Cancelled Successfully!**\n\n🎫 **Ticket Details:**\n• Ticket ID: {ticket_id}\n• User ID: {user_id}\n\n📧 **Next Steps:**\n• Confirmation email sent\n• Refund will be processed in 5-7 business days\n• Check your email for details"
                    else:
                        success_msg = f"❌ **Cancellation Failed**\n\nError: {result.get('message', 'Unknown error')}"
                else:
                    success_msg = f"❌ **API Error**\n\nServer returned status: {response.status_code}"
                    
            except requests.RequestException as e:
                success_msg = f"❌ **Connection Error**\n\nCould not connect to cancellation service: {str(e)}"
        else:
            # Demo mode
            success_msg = f"✅ **Flight Cancelled Successfully!**\n\n🎫 **Ticket Details:**\n• Ticket ID: {ticket_id}\n• User ID: {user_id}\n\n📧 **Next Steps:**\n• Confirmation email sent\n• Refund will be processed in 5-7 business days\n• Check your email for details"
        
        reset_cancellation_flow()
        return success_msg + "\n\nWhat else can I help you with today?"
        
    except Exception as e:
        error_msg = f"❌ **Cancellation Failed**\n\nError: {str(e)}\n\nPlease try again or contact customer support."
        reset_cancellation_flow()
        return error_msg

def reset_cancellation_flow():
    """Reset cancellation flow and return to initial state"""
    st.session_state.cancellation_flow = {
        "active": False,
        "step": None,
        "ticket_id": None,
        "user_id": None
    }

def handle_policy_agent_query(user_message: str, intents: list) -> str:
    """Handle queries using PolicyAgent for non-cancellation intents"""
    try:
        st.info("🔍 Consulting travel database...")
        response = process_query_sync(user_message)
        return f"📋 **Travel Information**\n\n{response}"
    except Exception as e:
        return f"❌ **Error processing query**\n\nI encountered an error: {str(e)}"
    
def process_user_message(user_message: str) -> str:
    """Main function to process user messages with intent classification"""
    
    if st.session_state.cancellation_flow["active"]:
        return process_cancellation_flow(user_message)
    
    intents = classify_intent(user_message)
    
    if intents:
        intent_info = f"🎯 Detected: {intents[0].get('type', 'Unknown')} - {intents[0].get('sub_intent', 'Unknown')} (Confidence: {intents[0].get('confidence', 0):.2f})"
        st.markdown(f'<div class="intent-info">{intent_info}</div>', unsafe_allow_html=True)
    
    if intents:
        primary_intent = intents[0].get('type', 'Unknown')
        
        if primary_intent == "Cancel Trip":
            return start_cancellation_flow()
        else:
            return handle_policy_agent_query(user_message, intents)
    else:
        return handle_policy_agent_query(user_message, [])

st.markdown('<div class="main-header">✈️ NexusAI Travel Assistant</div>', unsafe_allow_html=True)


if st.session_state.cancellation_flow["active"]:
    flow = st.session_state.cancellation_flow
    step_display = flow["step"].replace('_', ' ').title()
    st.markdown(f'<div class="flow-indicator">🔄 Cancellation Flow: {step_display}</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message"><strong>👤 You:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
    else:
        content = message["content"]
        if "✅" in content or "Successfully" in content:
            st.markdown(f'<div class="success-message"><strong>🤖 NexusAI:</strong><br>{content}</div>', unsafe_allow_html=True)
        elif "❌" in content or "Failed" in content:
            st.markdown(f'<div class="error-message"><strong>🤖 NexusAI:</strong><br>{content}</div>', unsafe_allow_html=True)
        elif "❓" in content or "Required" in content:
            st.markdown(f'<div class="warning-message"><strong>🤖 NexusAI:</strong><br>{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-response"><strong>🤖 NexusAI:</strong><br>{content}</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 💬 Chat with NexusAI")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Type your message here...",
        placeholder="Ask about flight cancellations, status, seats, or policies...",
        key="user_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        send_button = st.form_submit_button("📤 Send", use_container_width=True)
    with col2:
        clear_button = st.form_submit_button("🗑️ Clear", use_container_width=True)

if send_button and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    response = process_user_message(user_input)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()

if clear_button:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm NexusAI, your travel assistant. How can I help you today?"}
    ]
    st.session_state.cancellation_flow = {
        "active": False,
        "step": None,
        "ticket_id": None,
        "user_id": None
    }
    st.rerun()

if clear_button:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I'm NexusAI, your travel assistant. How can I help you today?"}
    ]
    st.session_state.cancellation_flow = {
        "active": False,
        "step": None,
        "ticket_id": None,
        "user_id": None
    }
    st.rerun()


st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "Powered by NexusAI • Travel Assistance System"
    "</div>",
    unsafe_allow_html=True
)
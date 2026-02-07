import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from src.agent.investment_agent import create_investment_agent
from src.agent.state import AgentState

# Page configuration
st.set_page_config(
    page_title="Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Investment Assistant")
st.markdown("AI-powered investment analysis and recommendations")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key:", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    model = st.selectbox("Model:", ["gpt-4", "gpt-3.5-turbo"])
    temperature = st.slider("Temperature:", 0.0, 1.0, 0.7)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    if not api_key:
        st.warning("Please enter your OpenAI API Key in the sidebar")
        st.stop()
    st.session_state.agent = create_investment_agent(api_key=api_key, model=model, temperature=temperature)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about investments, stocks, or portfolio analysis..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process with agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Create initial state
                initial_state = AgentState(
                    messages=[{"role": "user", "content": prompt}],
                    user_input=prompt,
                    intermediate_steps=[]
                )
                
                # Run agent
                result = st.session_state.agent.invoke(initial_state)
                
                # Extract final response
                final_response = result.get("output", "Sorry, I couldn't generate a response.")
                
                st.markdown(final_response)
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown("*Disclaimer: This AI assistant provides general information only and is not financial advice. Always consult with a qualified financial advisor.*")

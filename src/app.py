from dotenv import load_dotenv
import streamlit as st

from agent.graph.graph import graph
from agent.investment_agent import create_investment_agent

load_dotenv()

st.set_page_config(
    page_title="Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Investment Assistant")
st.markdown("AI-powered investment analysis and recommendations")

with st.sidebar:
    st.header("Configuration")
    model = st.selectbox("Model:", ["meta-llama/Llama-3.1-8B-Instruct"])
    temperature = st.slider("Temperature:", 0.0, 2.0, 0.1)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_investment_agent(
        model=model, temperature=temperature
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(
    "Ask me about investments, stocks, or portfolio analysis..."
):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                result = graph.invoke({"user_input": prompt, "response": ""})
                final_response = result["response"]

                st.markdown(final_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": final_response}
                )

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# Footer
st.markdown("---")
st.markdown(
    "*Disclaimer: This AI assistant provides general information only and is not\
    financial advice. Always consult with a qualified financial advisor.*"
)

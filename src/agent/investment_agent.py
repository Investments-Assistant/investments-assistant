"""Investment Analysis Agent using LangGraph."""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import Tool
from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.tools.investment_tools import (
    calculate_portfolio_metrics,
    analyze_risk,
    get_diversification_score,
    generate_investment_recommendation
)


def create_investment_agent(api_key: str, model: str = "gpt-4", temperature: float = 0.7):
    """
    Create an investment analysis agent using LangGraph.
    
    Args:
        api_key: OpenAI API key
        model: Model name (gpt-4 or gpt-3.5-turbo)
        temperature: Model temperature
        
    Returns:
        Compiled LangGraph agent
    """
    
    # Initialize LLM
    llm = ChatOpenAI(
        api_key=api_key,
        model=model,
        temperature=temperature
    )
    
    # Create tools
    portfolio_tool = Tool(
        name="calculate_portfolio_metrics",
        func=lambda x: str(calculate_portfolio_metrics(eval(x))),
        description="Calculate portfolio metrics from holdings. Input should be a dictionary of ticker symbols and amounts."
    )
    
    risk_tool = Tool(
        name="analyze_risk",
        func=lambda x: str(analyze_risk(eval(x))),
        description="Analyze portfolio risk profile. Input should be a dictionary of holdings."
    )
    
    diversification_tool = Tool(
        name="get_diversification_score",
        func=lambda x: str(get_diversification_score(eval(x))),
        description="Calculate portfolio diversification score."
    )
    
    recommendation_tool = Tool(
        name="generate_recommendation",
        func=lambda x: generate_investment_recommendation(x, {}),
        description="Generate investment recommendations based on query."
    )
    
    tools = [portfolio_tool, risk_tool, diversification_tool, recommendation_tool]
    
    # Create system prompt
    system_prompt = """You are an expert investment advisor AI assistant. Your role is to:
    
    1. Analyze investment portfolios and provide insights
    2. Assess risk profiles and recommend allocations
    3. Evaluate diversification strategies
    4. Provide educational information about investments
    5. Generate personalized investment recommendations
    
    Always:
    - Provide balanced, educational perspectives
    - Acknowledge that you're not a substitute for professional financial advice
    - Ask clarifying questions when needed
    - Use the available tools to provide data-driven insights
    - Consider the user's risk tolerance and time horizon
    
    Available tools:
    - calculate_portfolio_metrics: Analyze portfolio composition and metrics
    - analyze_risk: Assess risk profile and allocation recommendations
    - get_diversification_score: Evaluate portfolio diversification
    - generate_recommendation: Generate investment recommendations
    """
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Create LLM chain
    chain = prompt | llm
    
    # Define node functions
    def process_input(state: AgentState) -> AgentState:
        """Process user input and generate response."""
        try:
            # Format messages for the chain
            messages = state.messages
            
            # Get response from LLM
            response = chain.invoke({
                "messages": messages
            })
            
            # Extract content
            content = response.content if hasattr(response, "content") else str(response)
            
            # Update state
            state.output = content
            state.intermediate_steps.append(("llm_response", content))
            
            return state
            
        except Exception as e:
            state.output = f"I encountered an error while processing your request: {str(e)}"
            return state
    
    def format_output(state: AgentState) -> AgentState:
        """Format final output."""
        if not state.output:
            state.output = "I couldn't generate a response. Please try again."
        return state
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("process", process_input)
    workflow.add_node("format", format_output)
    workflow.add_node("end", lambda x: x)
    
    # Add edges
    workflow.set_entry_point("process")
    workflow.add_edge("process", "format")
    workflow.add_edge("format", "end")
    
    # Compile graph
    app = workflow.compile()
    
    return app


__all__ = ["create_investment_agent"]

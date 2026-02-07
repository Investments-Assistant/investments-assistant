"""Investment analysis tools for the agent."""

from typing import Dict, Any
import json
from datetime import datetime


def calculate_portfolio_metrics(holdings: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate basic portfolio metrics from holdings.
    
    Args:
        holdings: Dictionary with ticker symbols as keys and amounts as values
        
    Returns:
        Portfolio metrics dictionary
    """
    total_value = sum(holdings.values())
    allocation = {ticker: (amount / total_value * 100) for ticker, amount in holdings.items()}
    
    return {
        "total_value": total_value,
        "allocation": allocation,
        "num_holdings": len(holdings),
        "largest_position": max(holdings.items(), key=lambda x: x[1])[0] if holdings else None
    }


def analyze_risk(holdings: Dict[str, float], risk_profile: str = "moderate") -> Dict[str, Any]:
    """
    Analyze portfolio risk based on holdings and risk profile.
    
    Args:
        holdings: Dictionary of holdings
        risk_profile: User's risk profile (conservative, moderate, aggressive)
        
    Returns:
        Risk analysis dictionary
    """
    risk_factors = {
        "conservative": {"stocks": 0.3, "bonds": 0.7},
        "moderate": {"stocks": 0.6, "bonds": 0.4},
        "aggressive": {"stocks": 0.9, "bonds": 0.1}
    }
    
    allocation = risk_factors.get(risk_profile, risk_factors["moderate"])
    
    return {
        "risk_profile": risk_profile,
        "recommended_allocation": allocation,
        "analysis": f"Your {risk_profile} profile recommends {allocation['stocks']*100}% stocks and {allocation['bonds']*100}% bonds.",
        "timestamp": datetime.now().isoformat()
    }


def get_diversification_score(holdings: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate diversification score for a portfolio.
    
    Args:
        holdings: Dictionary of holdings with sectors
        
    Returns:
        Diversification score and recommendations
    """
    num_holdings = len(holdings)
    
    # Simple scoring: more holdings = better diversification
    if num_holdings < 3:
        score = 20
        recommendation = "Consider adding more holdings for better diversification"
    elif num_holdings < 8:
        score = 60
        recommendation = "Your portfolio is moderately diversified"
    else:
        score = 85
        recommendation = "Your portfolio shows good diversification"
    
    return {
        "diversification_score": score,
        "num_holdings": num_holdings,
        "recommendation": recommendation
    }


def generate_investment_recommendation(query: str, context: Dict[str, Any]) -> str:
    """
    Generate investment recommendations based on query and context.
    
    Args:
        query: User's investment question
        context: Context data about portfolio/market
        
    Returns:
        Recommendation text
    """
    recommendations = {
        "diversification": "Diversification is key to managing risk. Consider allocating your investments across different asset classes, sectors, and geographies.",
        "long-term": "For long-term investing, consider dollar-cost averaging and maintaining a disciplined investment strategy.",
        "risk": "Understanding your risk tolerance is crucial. Align your portfolio with your financial goals and time horizon.",
        "bonds": "Bonds can provide stability and income. Consider your duration and credit risk carefully.",
        "stocks": "Stocks offer growth potential but come with volatility. Focus on quality companies and long-term prospects."
    }
    
    # Simple keyword matching for demonstration
    query_lower = query.lower()
    
    for keyword, recommendation in recommendations.items():
        if keyword in query_lower:
            return recommendation
    
    return "I recommend taking a balanced approach to investing that aligns with your financial goals and risk tolerance."


__all__ = [
    "calculate_portfolio_metrics",
    "analyze_risk",
    "get_diversification_score",
    "generate_investment_recommendation"
]

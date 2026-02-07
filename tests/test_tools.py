"""Tests for investment agent."""

import pytest
from src.tools.investment_tools import (
    calculate_portfolio_metrics,
    analyze_risk,
    get_diversification_score
)


class TestInvestmentTools:
    """Test investment analysis tools."""
    
    def test_calculate_portfolio_metrics(self):
        """Test portfolio metrics calculation."""
        holdings = {"AAPL": 10000, "MSFT": 5000, "GOOGL": 3000}
        result = calculate_portfolio_metrics(holdings)
        
        assert result["total_value"] == 18000
        assert len(result["allocation"]) == 3
        assert abs(result["allocation"]["AAPL"] - 55.56) < 1
        assert result["num_holdings"] == 3
        assert result["largest_position"] == "AAPL"
    
    def test_analyze_risk(self):
        """Test risk analysis."""
        holdings = {"AAPL": 10000, "MSFT": 5000}
        
        result = analyze_risk(holdings, "moderate")
        assert result["risk_profile"] == "moderate"
        assert "recommended_allocation" in result
        assert result["recommended_allocation"]["stocks"] == 0.6
        assert result["recommended_allocation"]["bonds"] == 0.4
    
    def test_get_diversification_score(self):
        """Test diversification scoring."""
        # Low diversification
        holdings_low = {"AAPL": "tech", "MSFT": "tech"}
        result_low = get_diversification_score(holdings_low)
        assert result_low["diversification_score"] < 50
        
        # High diversification
        holdings_high = {
            "AAPL": "tech",
            "MSFT": "tech",
            "JPM": "finance",
            "JNJ": "healthcare",
            "XOM": "energy",
            "WMT": "retail",
            "LMT": "defense",
            "PLD": "reits",
            "TSLA": "auto"
        }
        result_high = get_diversification_score(holdings_high)
        assert result_high["diversification_score"] > 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

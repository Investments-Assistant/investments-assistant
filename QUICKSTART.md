# Quick Reference Guide

## Installation & Setup

### First Time Setup (Recommended)
```bash
cd investments-assistant
bash setup.sh
```

### Manual Setup
```bash
cd investments-assistant
poetry config virtualenvs.in-project true
poetry install
cp .env.example .env
# Edit .env with your OpenAI API key
```

## Running the Application

```bash
poetry run streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Development Commands

```bash
# Install dev dependencies
make install-dev

# Run tests
make test

# Check code quality
make lint

# Format code
make format

# Clean up
make clean
```

Or use Poetry directly:
```bash
poetry install --with dev
poetry run pytest -v --cov=src tests/
poetry run flake8 src/ app.py
poetry run black src/ app.py
poetry run isort src/ app.py
```

## Project Structure

```
ai-agent/
├── app.py                      # Main Streamlit app
├── setup.sh                    # Quick setup script
├── Makefile                    # Common commands
├── requirements.txt            # Core dependencies
├── requirements-dev.txt        # Dev dependencies
├── pyproject.toml             # Project configuration
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # Full documentation
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py           # Pydantic state model
│   │   └── investment_agent.py # LangGraph agent
│   └── tools/
│       ├── __init__.py
│       └── investment_tools.py # Investment analysis tools
│
└── tests/
    ├── __init__.py
    └── test_tools.py          # Unit tests for tools
```

## Configuration

### Environment Variables (.env)

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=2048
STREAMLIT_SERVER_PORT=8501
```

### Streamlit Settings

Edit `~/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#0066ff"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"

[client]
showErrorDetails = true

[server]
port = 8501
headless = true
```

## Key Files Explained

### app.py
- Streamlit UI with chat interface
- Session state management
- Error handling and user feedback
- Configuration in sidebar

### src/agent/state.py
- Pydantic model for agent state
- Tracks messages, intermediate steps, and analysis data

### src/agent/investment_agent.py
- Creates LangGraph workflow
- Defines nodes (process, format, end)
- Integrates investment tools
- Returns compiled graph

### src/tools/investment_tools.py
- Portfolio metrics calculation
- Risk analysis
- Diversification scoring
- Investment recommendations

### src/config.py
- Centralized configuration management
- Environment-based config selection (dev/prod)
- Loads from .env file

## Usage Examples

### Ask for Portfolio Analysis
> "I have AAPL $10k, MSFT $5k, GOOGL $3k. How diversified is this?"

### Get Risk Assessment
> "What's my risk profile for a conservative investor?"

### Request Recommendations
> "Should I add bonds to my portfolio?"

### Educational Questions
> "Explain dollar-cost averaging"

## Troubleshooting

### Poetry not found
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### Module not found error
```bash
poetry install
# Or with dev tools:
poetry install --with dev
```

### Dependency not found
```bash
# Update and reinstall
poetry update
poetry install
```

### Port already in use
```bash
# Specify a different port
poetry run streamlit run app.py --server.port 8502
```

### Slow response times
- Switch to `gpt-3.5-turbo` in sidebar
- Reduce `AGENT_MAX_TOKENS` in `.env`
- Check API rate limits

## Adding New Features

### Add a New Tool
1. Create function in `src/tools/investment_tools.py`
2. Export in `src/tools/__init__.py`
3. Create Tool wrapper in `src/agent/investment_agent.py`

### Modify Agent Workflow
1. Edit `src/agent/investment_agent.py`
2. Add nodes with `workflow.add_node()`
3. Connect with `workflow.add_edge()`

### Add Tests
1. Create test in `tests/test_*.py`
2. Run with `make test`
3. Check coverage with `pytest --cov`

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [LangChain Documentation](https://python.langchain.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## Support

For issues or questions:
1. Check the README.md
2. Review test examples in `tests/`
3. Check Streamlit/LangChain documentation
4. Open an issue on GitHub

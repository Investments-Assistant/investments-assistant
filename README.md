# Investment Assistant

A Streamlit-based investment analysis assistant powered by LangChain, LangGraph, and OpenAI.

## Features

- 🤖 **AI-Powered Analysis**: Uses LLM models (GPT-4 or GPT-3.5-turbo) for investment insights
- 📊 **Portfolio Analysis**: Calculate metrics, risk profiles, and diversification scores
- 💬 **Conversational Interface**: Natural language interaction through Streamlit
- 🔗 **LangGraph Integration**: Structured agent workflow with defined states
- 🛠️ **Investment Tools**: Built-in tools for portfolio analysis and recommendations

## Project Structure

```
├── app.py                      # Main Streamlit app
├── setup.sh                    # Quick setup script
├── Makefile                    # Common commands
├── pyproject.toml              # Poetry configuration
├── .env.example                # Environment template
├── README.md                   # This file
│
├── src/
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py            # Pydantic state model
│   │   └── investment_agent.py # LangGraph agent
│   └── tools/
│       ├── __init__.py
│       └── investment_tools.py # Investment analysis tools
│
└── tests/
    ├── __init__.py
    └── test_tools.py           # Unit tests for tools
```

## Setup

### 1. Clone and Navigate
```bash
cd investments-assistant
```

### 2. Install Poetry (if not already installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Configure Poetry for In-Project Virtualenvs
```bash
poetry config virtualenvs.in-project true
```

### 4. Install Dependencies
```bash
poetry install
```

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 6. Run the Application
```bash
poetry run streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Run Frontend Helper

You can also use the included helper script to launch the Streamlit frontend:

```bash
./scripts/run_streamlit.sh
```

If you're using Poetry, the script will run Streamlit inside the project's virtualenv.

## Usage

1. **Enter API Key**: Paste your OpenAI API key in the sidebar (or configure it in `.env`)
2. **Select Model**: Choose between GPT-4 or GPT-3.5-turbo
3. **Adjust Temperature**: Fine-tune the model's creativity (0.0 = deterministic, 1.0 = creative)
4. **Ask Questions**: Ask the agent about:
   - Portfolio analysis
   - Risk assessment
   - Diversification strategies
   - Investment recommendations
   - General investment education

## Agent Architecture

### State Management
The agent uses a structured `AgentState` that tracks:
- **messages**: Conversation history
- **user_input**: Current user query
- **intermediate_steps**: Agent reasoning steps
- **output**: Final response
- **analysis_data**: Structured data from tools

### Workflow
```
User Input → Process Node → Format Output → Response
                 ↓
            (LLM Processing)
```

### Available Tools
- `calculate_portfolio_metrics`: Portfolio composition analysis
- `analyze_risk`: Risk profile and allocation recommendations
- `get_diversification_score`: Diversification evaluation
- `generate_recommendation`: Personalized recommendations

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model name (default: gpt-4)
- `AGENT_TEMPERATURE`: Model temperature 0-1 (default: 0.7)
- `AGENT_MAX_TOKENS`: Maximum response tokens (default: 2048)

## Development

### Install Dev Dependencies
```bash
poetry install --with dev
```

### Run Tests
```bash
make test
# or
poetry run pytest -v --cov=src tests/
```

### Lint Code
```bash
make lint
# or
poetry run flake8 src/ app.py
poetry run mypy src/ app.py
```

### Format Code
```bash
make format
# or
poetry run black src/ app.py
poetry run isort src/ app.py
```

### Adding New Tools
1. Create a new function in `src/tools/investment_tools.py`
2. Export it in `src/tools/__init__.py`
3. Add a Tool wrapper in `src/agent/investment_agent.py`

## Dependencies

Poetry manages the following dependencies:

**Core:**
- streamlit: Web UI framework
- langchain: LLM orchestration
- langgraph: Agent state graph
- openai: OpenAI API client
- pydantic: Data validation
- python-dotenv: Environment variables

**Dev:**
- pytest: Testing framework
- black: Code formatter
- flake8: Linter
- mypy: Type checker
- sphinx: Documentation

## Disclaimer

⚠️ **Important**: This AI assistant provides general information and educational content only. It is **not** a substitute for professional financial advice. Always consult with a qualified financial advisor before making investment decisions.

## License

MIT License - See LICENSE file in the repository.

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a quick reference guide.

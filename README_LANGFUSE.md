# Langfuse Agent Debugger

A LangGraph-based system that analyzes Langfuse agent execution traces using the **AgentDebug** error detection framework.

## Overview

This project bridges Langfuse's agent trajectory storage with AgentDebug's sophisticated error analysis capabilities. It automatically:

1. Fetches agent execution traces from Langfuse
2. Converts them to AgentDebug's expected format
3. Performs two-phase error analysis:
   - **Phase 1**: Fine-grained error detection for each step and module
   - **Phase 2**: Critical error identification (root cause analysis)
4. Generates comprehensive terminal reports

## AgentDebug Concepts

AgentDebug analyzes LLM agent trajectories using a structured approach:

### Agent Trajectory Format

Each agent step consists of 4 modules:
- **Memory**: Summarizes/recalls information from previous steps
- **Reflection**: Evaluates current situation and progress
- **Planning**: Decides what to do next
- **Action**: Executes the actual action

### Error Types

AgentDebug defines 17 specific error types across 5 categories:

**Memory Module (3 errors)**:
- `over_simplification`: Oversimplifies complex information
- `memory_retrieval_failure`: Fails to retrieve relevant information
- `hallucination`: Recalls events that never happened

**Reflection Module (4 errors)**:
- `progress_misjudge`: Incorrectly evaluates task progress
- `outcome_misinterpretation`: Misinterprets action results
- `causal_misattribution`: Attributes failures to wrong causes
- `hallucination`: Believes actions were performed that weren't

**Planning Module (3 errors)**:
- `constraint_ignorance`: Ignores task constraints
- `impossible_action`: Plans fundamentally impossible actions
- `inefficient_plan`: Creates unnecessarily complex plans

**Action Module (4 errors)**:
- `misalignment`: Action contradicts stated plan
- `invalid_action`: Uses non-existent actions
- `format_error`: Invalid action format
- `parameter_error`: Incorrect action parameters

**System Errors (4 errors)**:
- `step_limit`: Exceeds maximum step count
- `tool_execution_error`: External tool/API errors
- `llm_limit`: LLM response limitations
- `environment_error`: Environment bugs or crashes

### Two-Phase Analysis

1. **Phase 1 (Fine-grained Analysis)**: Analyzes each step's modules using LLM to detect specific error types
2. **Phase 2 (Critical Error Detection)**: Identifies the most critical error that caused task failure

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Install uv

If you don't have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Project

1. Clone or navigate to the project directory:

```bash
cd langfuse-agent-debugger
```

2. Sync dependencies with uv:

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Make the project ready to use

3. Setup environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# OpenAI API (for error analysis)
OPENAI_API_KEY=sk-your-actual-key
OPENAI_MODEL=gpt-4o

# Langfuse API
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-key
LANGFUSE_SECRET_KEY=sk-lf-your-actual-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Usage

### Basic Usage

Analyze a Langfuse trace by its ID:

```bash
uv run main.py <trace-id>
```

Example:

```bash
uv run main.py trace-abc-123-def-456
```

### Alternative (without uv)

If you prefer using Python directly:

```bash
# Activate virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the script
python main.py trace-abc-123-def-456
```

### Output

The tool will:
1. Load the trace from Langfuse
2. Convert it to AgentDebug format
3. Run Phase 1 analysis (error detection per step)
4. Run Phase 2 analysis (critical error identification)
5. Display a formatted report in the terminal

Example output:

```
╔══════════════════════════════════════════════════════════════════════╗
║        LANGFUSE AGENT TRAJECTORY ERROR ANALYSIS REPORT               ║
╚══════════════════════════════════════════════════════════════════════╝

Trace ID: trace-abc-123
Task: Find a product under $50 and add to cart
Total Steps: 12
Task Success: ✗ No

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CRITICAL ERROR IDENTIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Critical Step: 3
Module: planning
Error Type: constraint_ignorance
Confidence: 0.85

Root Cause:
  Agent planned to select a $75 product despite the $50 budget constraint,
  ignoring the task requirement and leading to task failure.

Evidence:
  "I will click on this laptop for $74.99"

💡 Correction Guidance:
  The agent should filter products by price before selection, ensuring all
  candidates are within the budget constraint. Consider implementing a
  price-check step before finalizing product selection.

Cascading Effects:
  • Step 4: Continued with invalid product selection
  • Step 5: Added over-budget item to cart
  • Step 6-12: Attempted to proceed with invalid cart state

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STEP-BY-STEP ERROR SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 3:
  ⚠️  planning: constraint_ignorance
      Agent ignored the $50 budget constraint when selecting product

Step 7:
  ⚠️  reflection: outcome_misinterpretation
      Agent believed item was added successfully despite error message

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Langfuse Trace Requirements

### Expected Trace Structure

For optimal results, your Langfuse traces should follow these conventions:

#### 1. Trace Metadata

```python
{
  "metadata": {
    "task": "Task description",
    "success": True/False,  # Optional
    "environment": "your-env-name"  # Optional
  }
}
```

#### 2. Observations (Agent Steps)

Each agent step should be a `GENERATION` observation with:

**Input**: The user message (environment state or task description)

**Output**: Agent response in XML format (preferred) or structured dict:

```xml
<memory>Summary of previous steps</memory>
<reflection>Evaluation of current situation</reflection>
<plan>What to do next</plan>
<action>Actual action to execute</action>
```

Or as a dictionary:

```python
{
  "memory": "...",
  "reflection": "...",
  "plan": "...",
  "action": "..."
}
```

**Metadata** (optional but helpful):

```python
{
  "memory": "...",
  "reflection": "...",
  "plan": "...",
  "action": "...",
  "is_agent_step": True
}
```

#### 3. Environment Responses

Environment responses should appear as:
- The `input` of the next observation
- Or as `EVENT` type observations

### Flexible Conversion

The converter is designed to handle various Langfuse trace structures:

- If observations don't follow the exact format, it will attempt best-effort conversion
- Missing modules (e.g., no explicit memory/reflection tags) will be handled gracefully
- The system wraps unstructured output in `<action>` tags if needed

## Project Structure

```
langfuse-agent-debugger/
├── pyproject.toml              # uv project configuration
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── main.py                     # CLI entry point
├── detector/                   # AgentDebug core (existing)
│   ├── __init__.py
│   ├── error_definitions.py    # Error type definitions
│   ├── fine_grained_analysis.py   # Phase 1 analyzer
│   └── critical_error_detection.py # Phase 2 analyzer
├── langfuse_adapter/           # Langfuse integration
│   ├── __init__.py
│   ├── trace_loader.py         # Fetches traces from Langfuse
│   └── trajectory_converter.py # Converts to AgentDebug format
└── agent/                      # LangGraph pipeline
    ├── __init__.py
    ├── state.py                # State definition
    ├── nodes.py                # Pipeline nodes
    └── graph.py                # Graph construction
```

## Architecture

### LangGraph Pipeline

The system uses a 5-node LangGraph pipeline:

```
┌──────────┐    ┌─────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│  Load    │ -> │ Convert │ -> │ Phase1 │ -> │ Phase2 │ -> │ Report │
│  Trace   │    │ Format  │    │ Error  │    │Critical│    │  Gen   │
└──────────┘    └─────────┘    └────────┘    └────────┘    └────────┘
```

1. **Load**: Fetches trace from Langfuse API
2. **Convert**: Transforms to AgentDebug format
3. **Phase1**: Detects errors in each step/module
4. **Phase2**: Identifies critical root cause
5. **Report**: Generates formatted output

### Error Handling

Each node handles errors gracefully:
- Errors are logged to the state
- Pipeline continues even if a node fails
- Final report shows partial results + errors

## Troubleshooting

### Common Issues

#### 1. Missing Environment Variables

```
❌ Error: Missing required environment variables:
  - OPENAI_API_KEY
  - LANGFUSE_PUBLIC_KEY
```

**Solution**: Create `.env` file with required keys (see `.env.example`)

#### 2. Trace Not Found

```
Failed to load trace: Trace not found: trace-xyz
```

**Solution**:
- Verify the trace ID exists in Langfuse
- Check your Langfuse credentials
- Ensure you have access to the trace

#### 3. Conversion Errors

```
Failed to convert trajectory: No observations found
```

**Solution**:
- Check that your trace has observations
- Verify observations have `output` fields
- Review Langfuse trace structure requirements above

#### 4. OpenAI API Errors

```
API call failed: Unauthorized
```

**Solution**:
- Verify your `OPENAI_API_KEY` is correct
- Check if you have sufficient credits
- If using custom endpoint, verify `OPENAI_BASE_URL`

#### 5. Proxy Issues

If you're behind a corporate proxy:

```env
HTTPS_PROXY=http://your-proxy:port
```

### Debug Mode

For more detailed logging, modify `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(name)s - %(levelname)s - %(message)s'
)
```

### Getting Help

1. Check the error messages in the terminal
2. Review the `.env` file configuration
3. Verify your Langfuse trace structure
4. Check detector logs for LLM API issues

## Development

### Adding Dependencies

```bash
uv add <package-name>
```

Example:

```bash
uv add numpy
```

### Running Tests

```bash
uv run pytest
```

### Code Style

The project follows standard Python conventions. To format code:

```bash
uv run black .
uv run ruff check .
```

## API Configuration

### Using Custom OpenAI-Compatible APIs

You can use any OpenAI-compatible API:

```env
OPENAI_BASE_URL=https://your-api.com/v1/chat/completions
OPENAI_MODEL=your-model-name
```

Examples:
- Azure OpenAI
- Local LLM servers (LM Studio, Ollama with OpenAI compatibility)
- Third-party providers (Together AI, Anyscale, etc.)

## Performance Considerations

- **API Calls**: Each step requires 2-4 LLM calls (one per module)
- **Token Usage**: Depends on trajectory length and complexity
- **Time**: Typical analysis takes 30-60 seconds for 10-step trajectories
- **Rate Limits**: Be aware of OpenAI/Langfuse rate limits

## License

This project extends the AgentDebug framework for Langfuse integration.

## Citation

If you use this tool in research, please cite the original AgentDebug paper:

```bibtex
@article{agentdebug2024,
  title={AgentDebug: Systematic Error Analysis for LLM Agents},
  author={...},
  year={2024}
}
```

## Contributing

Contributions are welcome! Areas for improvement:

- Support for more Langfuse trace formats
- Additional error type definitions
- Performance optimizations
- Better visualization options
- Export to JSON/CSV formats

## Acknowledgments

- **AgentDebug** framework for error detection methodology
- **Langfuse** for agent observability platform
- **LangGraph** for workflow orchestration

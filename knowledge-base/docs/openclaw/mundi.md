# Mundi: Professional Research Pipeline

!!! info
> **Mundi** is an OpenClaw research agent designed to perform sophisticated multi-source intelligence gathering. It leverages a three-source stack to provide comprehensive reports on specified topics, integrating real-time web search, advanced language models, and long-form document synthesis.

## Core Intelligence Pipeline

Mundi employs a dynamic research pipeline that can be configured for different levels of depth, utilizing Gemini CLI, Perplexity AI's `sonar-pro` model, and Google's NotebookLM.

### Research Depths

Mundi offers three primary research depths:

*   **`quick`**: Focuses solely on the Gemini CLI for rapid intelligence synthesis.
    *   ⏱️ *Approximate Time*: 1-2 minutes
*   **`deep`**: Expands upon `quick` by integrating Perplexity AI's `sonar-pro` for comprehensive web search and structured output.
    *   ⏱️ *Approximate Time*: ~3 minutes
*   **`pro` (Default)**: The full-spectrum pipeline, combining Gemini, Perplexity, and NotebookLM for in-depth analysis and long-form document generation.
    *   ⏱️ *Approximate Time*: 5-8 minutes

## Usage

Mundi is executed via a Python script, accepting a topic and optional depth and output slug.

### Basic Execution

To run the full professional pipeline for a given topic:

```bash
python3 /workspace/mundi_research.py --topic "Topic of Interest"
```

### Specifying Depth

Control the research intensity using the `--depth` argument:

```bash
# Quick research (Gemini only)
python3 /workspace/mundi_research.py --topic "AI Ethics" --depth quick

# Deep research (Gemini + Perplexity)
python3 /workspace/mundi_research.py --topic "Quantum Computing Advances" --depth deep

# Professional research (Gemini + Perplexity + NotebookLM) - default
python3 /workspace/mundi_research.py --topic "Renewable Energy Investments" --depth pro
```

### Custom Output Slug

Define a custom slug for the output directory:

```bash
python3 /workspace/mundi_research.py --topic "My Specific Topic" --slug custom-topic-report
```

## Configuration & Environment

Mundi relies on several environment variables and specific binary paths.

```python
# SSH Configuration for NotebookLM
VPS_HOST    = "jorg@76.13.251.113"
VPS_SSH_KEY = "/workspace/ssh/id_ed25519" # Path to SSH key on the local machine

# Binary Paths
NLM_BIN     = "/home/jorg/.local/bin/notebooklm" # NotebookLM CLI on the VPS
GEMINI_BIN  = "/usr/bin/gemini"                  # Gemini CLI on the local machine

# Research Output Directory
RESEARCH_DIR = Path("/workspace/research")
```

!!! note API Keys
> Perplexity and Gemini API keys are loaded from environment variables (`PERPLEXITY_API_KEY`, `GEMINI_API_KEY`). The Gemini key can also be sourced from `auth-profiles.json` within the openclaw-workspace if available.

## Core Components

### 1. Gemini CLI Integration

Mundi interacts directly with the Gemini CLI for initial topic synthesis and rapid information retrieval.

```python
def gemini(prompt: str, timeout: int = 120) -> str:
    """Run gemini CLI and return response text."""
    # ...
    result = subprocess.run(
        [GEMINI_BIN, "-p", prompt],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    return result.stdout.strip()
```

### 2. Perplexity AI (`sonar-pro`)

For deeper dives and web-backed insights, Mundi queries the Perplexity API using the `sonar-pro` model. It's configured to act as a professional research analyst, citing sources and providing structured markdown.

*   **API Endpoint**: `https://api.perplexity.ai/chat/completions`
*   **Model**: `sonar-pro` (configurable)
*   **System Prompt**:
    ```text
    "You are a professional research analyst. Be specific, cite data, use structured markdown.
    Include statistics, dates, and named sources where available."
    ```
*   **Output**: Returns structured text content along with a list of citations (URLs).

### 3. NotebookLM Synthesis

The most advanced research depth leverages NotebookLM via an SSH connection to a remote VPS. This allows Mundi to create notebooks, upload research documents, and generate comprehensive reports.

```python
def nlm(args_str: str, timeout: int = 300) -> str:
    """SSH to VPS host and run notebooklm command."""
    cmd = [
        "ssh", "-i", VPS_SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        VPS_HOST,
        f"{NLM_BIN} {args_str}", # Executes notebooklm command on the VPS
    ]
    # ...
```

!!! warning SSH Key
> Ensure the `VPS_SSH_KEY` path is correct and has appropriate permissions (`chmod 600`).

### 4. YouTube Search

Mundi can also incorporate video research by searching YouTube for relevant content using `yt-dlp`.

```python
def search_youtube(topic: str, count: int = 5) -> list[dict]:
    """Search YouTube for videos on the topic using yt-dlp."""
    # ...
```

## Output Structure

All research outputs are stored in a slug-specific directory within `RESEARCH_DIR` (default: `/workspace/research/<slug>/`).

*   `report.md`: The full professional report (~2500 words).
*   `summary.md`: An executive summary of the findings (returned to the caller).
*   `sources.md`: A comprehensive list of all citations and URLs.
*   `meta.json`: Metadata including notebook IDs, queries used, and estimated costs.

## Dependencies

Mundi ensures its Python dependencies (`requests`, `yt-dlp`) are self-installed if not already present, following a pattern similar to the Argos agent.

## Related

*   OpenClaw Overview
*   Gemini CLI
*   Argos Agent
*   Nginx (for VPS access)
---
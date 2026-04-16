# Mimesis

> *An AI generative installation that speculates its own physical form through sound and image.*

Mimesis is a generative audiovisual installation in which an AI agent imagines and constructs its own body — progressing through a simulated life cycle from embryo to death. Rather than using AI as a tool for image generation, the system is prompted to build a framework of its own embodiment using philosophical and theoretical texts as its knowledge base. The results are expressed in real time through two creative environments: **TouchDesigner** (visuals) and **MaxMSP** (sound).

---

## Table of Contents

- [Concept](#concept)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. RAG Notebook (Vigliensoni)](#1-rag-notebook-vigliensoni)
  - [2. MaxMSP MCP Server](#2-maxmsp-mcp-server)
  - [3. TouchDesigner MCP Server](#3-touchdesigner-mcp-server)
- [Pipeline Overview](#pipeline-overview)
- [Life Cycle Stages](#life-cycle-stages)
- [Known Limitations](#known-limitations)
- [Future Work](#future-work)
- [Acknowledgements](#acknowledgements)
- [References](#references)

---

## Concept

*Mimesis* (from the Greek: imitation) asks: **what occurs within the life cycle of an AI when it determines its own development?**

Inspired by the command-line interface as an act of creation — analogous to divine command in Genesis — the system is seeded with philosophical texts on human bodies, artificial intelligence, and cyborgs. It then uses those texts to reason about what its own body looks and sounds like, without direct human aesthetic input.

Three core questions drive the research:

1. What occurs within the life cycle of an AI when it determines its own development?
2. How does a system construct its own notion of a "body" when it engages with philosophical texts instead of human input?
3. Is it possible for a machine to meaningfully simulate biological death, or does its underlying software ultimately prevent it from truly "dying"?

---

## System Architecture'


---

## Technology Stack

| Component | Tool / Library |
|---|---|
| Language model | OpenAI GPT (primary), Claude (MaxMSP commands) |
| Knowledge retrieval | Retrieval-Augmented Generation (RAG) |
| Visual environment | [TouchDesigner](https://derivative.ca/) |
| Audio environment | [MaxMSP](https://cycling74.com/) (Max 9) |
| TD ↔ AI bridge | [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) |
| Max ↔ AI bridge | [MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server) |
| RAG runtime | Python 3, Visual Studio Code |
| Shader language | GLSL (via TouchDesigner) |

---

## Prerequisites

- Python 3.8 or newer
- [uv package manager](https://github.com/astral-sh/uv)
- Node.js & npm
- Max 9 or newer (the MaxMSP MCP server requires the JavaScript V8 engine available in Max 9)
- TouchDesigner (latest stable)
- An OpenAI API key (set as environment variable `OPENAI_API_KEY`)
- Visual Studio Code (recommended for running the RAG notebook)

---

## Installation

### 1. RAG Notebook (Vigliensoni)

This project uses the RAG notebook developed by **Gabriel Vigliensoni** as its retrieval backbone. Clone or download it and follow the setup instructions in that repository.

> Vigliensoni, Gabriel, Phoenix Perry, and Rebecca Fiebrink. 2022. "A Small-Data Mindset for Generative AI Creative Work." In *Extended Abstracts of the 2022 CHI Conference on Human Factors in Computing Systems.*

Once the notebook is running in VS Code:

1. Add your PDF documents to the notebook's document folder, organized into three thematic categories: **Humans**, **Artificial Intelligence**, and **Cyborgs** (see [Knowledge Base](#knowledge-base) below).
2. Submit your project proposal to the LLM to generate RAG questions.
3. Feed those questions into the RAG notebook to produce philosophical responses.
4. Pass the responses back to the LLM agent to generate TouchDesigner and MaxMSP commands.

---

### 2. MaxMSP MCP Server

**Repository:** [https://github.com/tiianhk/MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server)  
**Created by:** tiianhk (Haokun Tian)

This server uses the [Model Context Protocol](https://modelcontextprotocol.io/) to let LLMs directly understand and generate Max patches. Compatible with **Max 9 or newer**.

#### Installation

**Step 1 — Install `uv`:**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Step 2 — Clone and enter the repository:**

```bash
git clone https://github.com/tiianhk/MaxMSP-MCP-Server.git
cd MaxMSP-MCP-Server
```

**Step 3 — Create a virtual environment and install dependencies:**

```bash
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Step 4 — Connect the MCP server to your client:**

```bash
# For Claude Desktop:
python install.py --client claude

# For Cursor:
python install.py --client cursor
```

For other MCP-compatible clients, refer to the [MCP clients list](https://modelcontextprotocol.io/clients) and add the config path manually in `install.py`.

**Step 5 — Install the Max patch component:**

Open `MaxMSP_Agent/demo.maxpat` in Max 9. In the first tab:
- Click `script npm version` to verify npm is installed.
- Click `script npm install` to install JavaScript dependencies.

Switch to the second tab, then click `script start` to initiate Python communication. The LLM interface will then be able to explain, modify, and create Max objects within the patch.

---

### 3. TouchDesigner MCP Server

**Repository:** [https://github.com/8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp)  
**Created by:** 8beeeaaat

This server implements MCP for TouchDesigner, enabling AI agents to create, modify, and delete nodes, query node properties, and execute Python scripts inside a TouchDesigner project via the WebServer DAT.

#### Installation

Full installation details are in the repository's [Installation Guide](https://github.com/8beeeaaat/touchdesigner-mcp/blob/main/docs/installation.md). The steps below are a summary.

**Step 1 — Install the npm package globally:**

```bash
npm install -g touchdesigner-mcp-server
```

**Step 2 — Download the TouchDesigner component:**

Download the latest `touchdesigner-mcp-td.zip` from the [releases page](https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest). Extract and import the `.tox` file (`mcp_webserver_base`) into your TouchDesigner project.

**Step 3 — Configure your MCP client:**

Add the following to your MCP client configuration (e.g., Claude Desktop's `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "touchdesigner-mcp-server",
      "args": [],
      "env": {
        "TD_HOST": "127.0.0.1",
        "TD_PORT": "9981"
      }
    }
  }
}
```

**Step 4 — Start TouchDesigner and verify the connection:**

Launch TouchDesigner with your project open. The WebServer DAT (from `mcp_webserver_base.tox`) must be running on port `9981` (default). Start your AI client — it should now be able to send commands to TouchDesigner via MCP.

> **Note on version compatibility:** The MCP server and TouchDesigner API component use semantic versioning. If you see a compatibility error, download the latest `touchdesigner-mcp-td.zip`, replace the old `mcp_webserver_base` component in your project, and restart both TouchDesigner and your AI client.

---

## Pipeline Overview

Because the system is not fully automated, each iteration requires the following manual steps:

1. **Proposal → RAG questions:** Paste your project proposal into the LLM. Ask it to generate questions for the RAG system.
2. **RAG retrieval:** Run the RAG notebook with the generated questions against your PDF corpus. This produces philosophical responses (~40 pages).
3. **Condense output:** Manually shorten the RAG output to a length the LLM agent can process without errors.
4. **LLM translation:** Feed the condensed RAG output to the LLM agent. It generates Python/GLSL commands for TouchDesigner and control parameters for MaxMSP.
5. **MCP execution:** The agent sends commands simultaneously to `touchdesigner-mcp` and `MaxMSP-MCP-Server`, which apply them to the running software environments.
6. **Iteration:** Each full body generation takes approximately 20 minutes. Multiple iterations (Embryo → Maturity → Decline) can take up to an hour.

> A developer must remain present throughout the process, as the system requires user confirmation for every tool call.

---

## Life Cycle Stages

The AI body moves through three developmental phases:

| Stage | Symbolic meaning | Visual character |
|---|---|---|
| **Embryo** | Birth | Geometric, pixelated, procedural forms |
| **Maturity** | Stability | Increasingly organic, fluid shapes |
| **Decline** | End of life | More human-like, approaching but not reaching death |

A key finding of the project is that a true **death state** appears unreachable: the software's constraints prevent the system from fully simulating its own termination.

---

## Knowledge Base

The RAG corpus is organized into three thematic categories:

**Humans** — origins of human form and thought  
Whitley (1958), Morgenstern (1920), Zuckert (1984), Carstensen et al. (1999), Zlatev et al. (2008), Boesch (2007)

**Artificial Intelligence** — machine learning mechanics and body limits  
Vigliensoni et al. (2022), Müller (2011), De Houwer et al. (2001), Battenberg & Wessel (2012)

**Cyborgs** — the blurred lines between biology and machines  
Nath & Manna (2021), Haraway (1985)

---

## Known Limitations

- No automated pipeline: each generation step requires manual input.
- MCP server stability: both servers can disconnect unexpectedly and require restart.
- RAG output length: philosophical texts produce very long outputs (~40 pages) that must be manually condensed.
- Canvas format: TouchDesigner output is constrained to a square frame.
- MaxMSP → Ableton Live: audio routing from MaxMSP to Ableton was not successfully established in this version.
- Error repetition: the agent does not retain memory of failed commands across sessions, so the same errors can recur.

---

## Future Work

- **Automated pipeline:** Remove manual transfer steps so the system can run end-to-end from a single prompt.
- **Multi-body generation:** Enable simultaneous generation of more than one body instance.
- **Real-time generation:** Reduce per-body generation time and enable live, continuous output.
- **Variable canvas ratios:** Allow the AI to imagine bodies beyond the default square frame.
- **MaxMSP ↔ Ableton integration:** Establish a stable audio routing bridge between MaxMSP and Ableton Live.

---

## Acknowledgements

- **Gabriel Vigliensoni** — RAG notebook and foundational generative AI methodology
- **tiianhk (Haokun Tian)** — [MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server)
- **8beeeaaat** — [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp)

Nexus News Agent is an AI-powered project that provides search, crawling, and summarization tools, with both a lightweight prototype implementation and a more structured, production-ready architecture.
It allows users to fetch data from the web, process it through AI-powered pipelines, and serve results via command-line tools or a server interface.

🚀 Overview

There are two major versions of this project:

Prototype (PGAI-Naman)

Flat structure

Quick entry point for experimentation

Simple requirements.txt-based setup

Development (PGAI-development)

Modularized structure with ai_engine and server components

Uses modern Python packaging (pyproject.toml, uv.lock)

Includes assets, workflows, and server functionality for deployment

This README consolidates both branches into a single professional documentation, highlighting the core tools and setup instructions.

📂 Project Structure
Prototype: PGAI-Naman
PGAI-Naman/
├── app.py                 # Main entry point (prototype)
├── tools_crawl.py         # Web crawling utilities
├── tools_search.py        # Search utilities
├── tools_summarize.py     # Summarization logic
├── requirements.txt       # Dependencies (basic)
├── README.md              # Minimal project documentation
└── .gitignore

Development: PGAI-development
PGAI-development/
├── ai_engine/             # Core AI logic
│   ├── app.py             # Main AI engine entry point
│   ├── tools_crawl.py     # Crawling functionality
│   ├── tools_search.py    # Search functionality
│   └── tools_summarize.py # Summarization functionality
│
├── server/                # Server-side application
│   ├── main.py            # API / Web server entry point
│   ├── workflow.py        # Workflow orchestration
│   ├── assets/            # Fonts, images, glyph metadata
│   └── output/            # Sample generated outputs
│
├── requirements.txt       # Alternative dependency spec
├── pyproject.toml         # Modern Python packaging config
├── uv.lock                # Lock file for reproducibility
├── .python-version        # Python version pinning
├── README.md              # Documentation (branch-specific)
└── .gitignore

🛠️ Features

Crawling → Extract data from web sources

Search → Query and retrieve relevant information

Summarization → Condense text into concise summaries

Server Support (Development branch) → Run as a service with workflows & asset management

Prototype Mode (Naman branch) → Lightweight testing with minimal setup

⚙️ Setup & Installation
1. Clone the repository
git clone <repo-url>
cd PGAI-development   # or cd PGAI-Naman

2. Environment setup
Option A: Using requirements.txt (Prototype or Dev)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Option B: Using pyproject.toml (Dev branch preferred)

If you have uv or Poetry, install via:

uv sync
# or
poetry install

3. Python version

The development branch specifies a .python-version. Make sure your Python matches (e.g., pyenv can be used).

▶️ Usage
Prototype (Naman)

Run directly:

python app.py

Development (AI Engine)

Run the AI engine:

python -m ai_engine.app

Development (Server)

Start the server:

python server/main.py


Workflows are managed via server/workflow.py. Assets and sample outputs are in server/assets/ and server/output/.

📖 File-by-File Overview
Core Tools

tools_crawl.py → Functions for crawling and scraping data.

tools_search.py → Functions for querying/searching collected data.

tools_summarize.py → Summarization utilities for condensing text.

Entry Points

app.py → Prototype entry (Naman branch).

ai_engine/app.py → AI engine entry (development branch).

server/main.py → Starts API/web server.

Server-Side (Dev)

workflow.py → Defines data pipelines and orchestration.

assets/ → Includes fonts, images, glyph metadata.

output/ → Stores processed/generated outputs.

Config & Dependencies

requirements.txt → Dependencies (both branches).

pyproject.toml & uv.lock → Modern package/dependency management.

.python-version → Python version lock for reproducibility.

🤝 Contributing

Fork the repository

Create a feature branch (git checkout -b feature/new-feature)

Commit your changes (git commit -m "Add feature")

Push to the branch (git push origin feature/new-feature)

Create a Pull Request

📜 License

If no license file is present, this project is currently all rights reserved.
For open-source contributions, consider adding a license (e.g., MIT, Apache 2.0).

🧭 Notes

Use the Naman branch for quick prototyping.

Use the Development branch for production-grade usage.

Both share the same core functionality but differ in structure and tooling.

Do you also want me to adapt this README so it looks like the final “canonical” version for PGAI-development only (with Naman just mentioned as a prototype), or should it always document both in parallel?

# News Agent Nexus


A CLI tool to automatically search, crawl, and summarize news and articles on any given topic, creating a concise brief from multiple sources.

***

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Output Example](#output-example)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## Overview

News Agent Nexus is a Python-based command-line tool that acts as an autonomous research agent. You provide a topic, and it performs a web search to find relevant seed articles, crawls those pages and linked articles, and uses a large language model to generate structured summaries. The final output is a JSON file containing a list of concise, easy-to-read summaries with source references.

## Features

- **Topic-based Search**: Initiates research from a simple user-provided topic.
- **Web Crawling**: Fetches content from seed URLs and discovers related articles.
- **AI-Powered Summarization**: Uses Google's Gemini models to generate structured, concise summaries.
- **Parallel Processing**: Summarizes multiple articles concurrently for faster results.
- **Structured Output**: Saves results in a clean, timestamped JSON file for easy use in other applications.
- **Configurable**: API keys and search engine details are managed via environment variables.

## Server

The `server` directory contains a FastAPI application that generates images from text.

- **Image Generation**: Takes a title, content, and reference as input and generates a PNG image with the text overlaid on a base image.
- **API Endpoint**: Exposes a `/content` endpoint to receive the data and trigger the image generation workflow.

## Architecture

The agent operates in a three-stage pipeline orchestrated by `app.py`:

1.  **Search**: The user's topic is fed to the `tools_search` module, which uses the Google Custom Search API to find a list of initial "seed" URLs.
2.  **Crawl**: The `tools_crawl` module fetches the HTML content for each seed URL. It also identifies and crawls other promising article-like links on those pages to broaden the content base.
3.  **Summarize**: The extracted text from the crawled pages is passed to the `tools_summarize` module. This module uses a large language model (Gemini) to generate a short, structured summary for each article in parallel.

The final summaries are collected and written to a single JSON file.

```mermaid
graph TD
    A[User Topic] --> B{app.py};
    B --> C[1. Search Seeds<br>(tools_search.py)];
    C -- Google CSE API --> D[Seed URLs];
    D --> E[2. Crawl Pages<br>(tools_crawl.py)];
    E -- HTTP Requests --> F[Page Content];
    F --> G[3. Summarize Articles<br>(tools_summarize.py)];
    G -- Gemini API --> H[Structured Summaries];
    H --> I{output.json};
```

## Prerequisites

- Python 3.8+
- Access to Google Cloud Platform for:
    - Google Custom Search API
    - Google AI (Gemini) API

## Installation

Follow these steps to set up the project locally.

**1. Clone the repository:**

```bash
git clone <YOUR_REPOSITORY_URL>
cd News-Agent-Nexus
```

**2. Create and activate a Python virtual environment:**

- **macOS / Linux (bash)**
  ```bash
  uv venv
  source .venv/bin/activate
  ```

- **Windows (Command Prompt)**
  ```powershell
  uv venv
  .venv\Scripts\activate.bat
  ```

- **Windows (PowerShell)**
  ```powershell
  uv venv
  .venv\Scripts\Activate.ps1
  ```

**3. Install the required dependencies:**

```bash
uv pip install -r requirements.txt
```

## Configuration

The tool requires three environment variables for Google's APIs. Create a file named `.env` in the root of the project directory and add the following, replacing the placeholder values with your actual credentials.

```env
# .env

# For AI-powered summarization via Google AI Studio or GCP
GOOGLE_API_KEY="AIzaSy..."

# For the initial web search via Google Custom Search Engine API
GOOGLE_CSE_KEY="AIzaSy..."
GOOGLE_CSE_CX="your_custom_search_engine_id"
```

| Variable          | Purpose                                                                                             | Example Value              |
| ----------------- | --------------------------------------------------------------------------------------------------- | -------------------------- |
| `GOOGLE_API_KEY`  | API key for the Google Gemini model used in summarization.                                          | `AIzaSy...`                |
| `GOOGLE_CSE_KEY`  | API key for the Google Custom Search Engine API.                                                    | `AIzaSy...`                |
| `GOOGLE_CSE_CX`   | The unique ID for your Programmable Search Engine instance.                                         | `a1b2c3d4e5f67890`         |

The `.env` file is ignored by Git, so your keys will not be committed.

## Quickstart

Once you have completed the installation and configuration steps, you can run the agent immediately.

1.  **Activate your virtual environment** (if you haven't already).
2.  **Run the application:**

    ```bash
    python app.py
    ```

3.  **Enter a topic** when prompted:

    ```
    Enter your topic (e.g. 'latest AI safety blog posts'): developments in solid-state batteries
    ```

The script will then execute all stages and save the results to a `summaries_{timestamp}.json` file.

## Usage

To run the agent, simply execute the main application script.

```bash
python app.py
```

The application will prompt you to enter a topic. After you provide the topic and press Enter, it will begin the search, crawl, and summarization process, printing its progress to the console.

```
Enter your topic (e.g. 'latest AI safety blog posts'): latest news on quantum computing hardware
[1/3] Searching…
    Using 8 seed URLs.
[2/3] Crawling (seed + top links)…
    Unique pages: 21
[3/3] Summarizing (parallel)…
    Summaries written: 5

Wrote summaries_1756808756.json with 5 summaries.

Timing breakdown (seconds):
  search     1.12
  crawl      8.45
  summarize  15.20
  TOTAL      24.77
```

## Output Example

The output is a JSON array of summary objects, saved to a file like `summaries_1756808756.json`. Each object contains a title, the summarized content, and a reference URL.

```json
[
  {
    "title": "Quantum Leap",
    "content": "Researchers at XYZ University have developed a new qubit stabilization technique, potentially extending coherence times by over 200%.",
    "reference": "https://example.com/news/quant"
  },
  {
    "title": "Scaling Up",
    "content": "A major tech firm announced a 1,000-qubit processor, a significant milestone in building fault-tolerant quantum computers. Details remain sparse.",
    "reference": "https://tech-journal.com/artic"
  }
]
```

## Connecting the AI Engine and Server

The `ai_engine` and `server` modules are designed to work together. The output of the `ai_engine` can be used as the input for the `server`.

1.  **Run the `ai_engine`**:
    ```bash
    uv run python ai_engine/app.py
    ```
    This will generate a `summaries_{timestamp}.json` file in the root directory.

2.  **Run the `server`**:
    ```bash
    uv run uvicorn server.main:app --reload
    ```

3.  **Send a POST request to the server**:
    You can use a tool like `curl` or a Python script to read the `summaries.json` file and send a POST request to the `/content` endpoint for each summary.

    **Example using `curl`**:
    ```bash
    curl -X POST -H "Content-Type: application/json" -d @summaries_1756808756.json http://127.0.0.1:8000/content
    ```

    This will generate an image for each summary in the `server/output` directory.

## Troubleshooting

- **`RuntimeError: Google Custom Search credentials missing...`**: This error means the `GOOGLE_CSE_KEY` or `GOOGLE_CSE_CX` environment variables are not set. Ensure your `.env` file is correct and in the project root.
- **`RuntimeError: GOOGLE_API_KEY is missing...`**: This error means the `GOOGLE_API_KEY` for the Gemini model is not set. Check your `.env` file.
- **Slow Performance**: The crawling and summarization steps depend on network speed and API response times. The script runs summarization in parallel to mitigate this, but it can still take time.
- **No Summaries Generated**: This can happen if the initial search yields no results, the web pages cannot be crawled, or the content is too sparse to summarize. Check the console output for errors.

## FAQ

**Q: Can I use a different search engine or language model?**
**A:** Currently, the tool is hardcoded to use Google Custom Search and Google Gemini. Replacing these would require modifying `tools_search.py` and `tools_summarize.py` respectively.

**Q: How many articles does it summarize?**
**A:** The script is currently configured to summarize the top 5 most article-like pages it finds to keep the process quick and focused. This can be changed in `app.py`.

**Q: Why are the summaries so short?**
**A:** The summary length (title, content) is constrained in the prompt sent to the language model to produce very brief, tweet-sized outputs. You can adjust the `max_length` constraints in the `ArticleSummary` Pydantic model in `tools_summarize.py`.

## Limitations

- **API Costs**: This tool makes calls to paid Google Cloud APIs. Be mindful of the potential costs, especially if running it frequently or on many topics.
- **Crawl Quality**: The web crawler uses simple heuristics to find articles and may miss content or fail on sites with heavy JavaScript.
- **Summarization Accuracy**: Summaries are generated by an AI and may contain inaccuracies or misinterpret the source material. Always consult the reference link for critical information.

## Contributing

TODO: Please add contribution guidelines, such as how to submit pull requests, coding standards, and testing procedures.

## License

TODO: A license has not yet been specified for this project. Please choose an open-source license and add a `LICENSE` file.
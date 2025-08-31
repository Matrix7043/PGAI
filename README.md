# News Agent Nexus

## Overview

News Agent Nexus is a command-line tool that automates the process of finding, crawling, and summarizing news articles on a given topic. It uses Google Custom Search to find relevant articles, crawls the websites to extract their content, and then uses a large language model to generate concise summaries.

## Features

- **Topic-based News Aggregation**: Provide any topic, and the agent will find the latest news.
- **Web Crawling**: Extracts the main content from news articles, filtering out boilerplate.
- **AI-Powered Summarization**: Uses a Large Language Model to generate high-quality summaries.
- **Configurable**: Easily customize parameters like the number of articles to process, crawl depth, and more.
- **Efficient and Robust**: Built with parallel processing, timeouts, and error handling to ensure it runs smoothly.
- **Extensible**: The agent is built with `langgraph`, making it easy to modify the workflow.

## How It Works

The agent operates in a three-step process, orchestrated by a state graph:

1.  **Search**: The agent starts by searching Google for news articles based on the user-provided topic. It filters out irrelevant domains to ensure the quality of the sources.

2.  **Crawl**: Next, it crawls the top search results to extract the full text of each article. The crawler is optimized for speed and can be configured to limit the number of pages and crawl depth.

3.  **Summarize**: In the final step, the agent summarizes the crawled content. It uses a parallelized approach to generate summaries quickly and respects a global time budget to ensure it completes in a timely manner.

The final summaries are saved to a JSON file in the project's root directory.

## Getting Started

### Prerequisites

- Python 3.7+
- An environment file with your Google API credentials.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/news-agent-nexus.git
    cd news-agent-nexus
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file is not yet present. You can create one by running `pip freeze > requirements.txt`)*

3.  **Set up your environment variables:**

    Create a file named `.env` in the root of the project and add the following, replacing `...` with your actual credentials:
    ```
    GOOGLE_API_KEY=...
    GOOGLE_CSE_ID=...
    GOOGLE_CSE_KEY=...
    ```

### Usage

To run the agent, simply execute the `app.py` script:

```bash
python app.py
```

You will be prompted to enter a topic. For example:

```
Enter your topic (e.g. 'latest AI safety blog posts'):
```

The agent will then start the process, and you'll see log messages for each stage. Once complete, a `summaries_{timestamp}.json` file will be created with the results.

## Configuration

You can adjust the agent's behavior by modifying the constants at the top of the `app.py` file. These include:

- `SEEDS`: The number of seed URLs to start with.
- `PAGES_PER_SEED`: The number of pages to crawl per seed URL.
- `CRAWL_DEPTH`: The maximum depth for the crawler.
- `SUMMARIES_MAX`: The maximum number of summaries to generate.
- `GLOBAL_BUDGET`: The maximum time in seconds the agent is allowed to run.

## Dependencies

This project relies on the following major Python libraries:

- `langgraph`: To create and manage the agent's workflow.
- `beautifulsoup4` and `trafilatura`: For web crawling and content extraction.
- `google-api-python-client`: For interacting with the Google Search API.
- `python-dotenv`: For managing environment variables.

To generate a full list of dependencies, you can run:
```bash
pip freeze > requirements.txt
```

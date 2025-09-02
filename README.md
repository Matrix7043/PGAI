# Nexus News Agent

Nexus News Agent is an AI-powered project that provides a suite of tools for searching, crawling, and summarizing news articles from the web. It features a powerful AI engine to process text and a server component to generate images with the summarized content.

## Features

- **Search**: Find news articles on any topic using Google Custom Search.
- **Crawl**: Fetch and parse the content of articles from their URLs.
- **Summarize**: Generate concise, one-line summaries of articles using the Gemini API.
- **Image Generation**: Create images with the title, summary, and source of an article overlaid on a template.
- **Modular Architecture**: The project is divided into an `ai_engine` for core processing and a `server` for API and image generation.

## Project Structure

```
PGAI/
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── requirements.txt
├── uv.lock
├── ai_engine/
│   ├── app.py              # Main entry point for the AI engine
│   ├── tools_crawl.py      # Web crawling utilities
│   ├── tools_search.py     # Search utilities
│   └── tools_summarize.py  # Summarization logic
└── server/
    ├── main.py             # FastAPI server
    ├── workflow.py         # Image generation workflow
    ├── assets/
    │   ├── base.png
    │   ├── glyphnames.json
    │   └── JetBrainsMonoNerdFontMono-BoldItalic.ttf
    └── output/
        └── processed_image.png
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- An environment manager like `venv` or `uv`.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd PGAI
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    You can use either `pip` with `requirements.txt` or `uv` with `pyproject.toml`.

    *   **Using `pip`:**
        ```bash
        pip install -r requirements.txt
        ```

    *   **Using `uv`:**
        ```bash
        uv sync
        ```

### Configuration

The project requires API keys for Google Custom Search and the Gemini API.

1.  **Create a `.env` file** in the root of the `PGAI` directory.
2.  **Add your API keys to the `.env` file:**
    ```
    GOOGLE_CSE_KEY="your_google_custom_search_engine_key"
    GOOGLE_CSE_CX="your_google_custom_search_engine_cx"
    GOOGLE_API_KEY="your_gemini_api_key"
    ```

## Usage

### AI Engine

The AI engine is a command-line tool that takes a topic as input, searches for relevant articles, crawls them, and generates summaries.

1.  **Run the AI engine:**
    ```bash
    python -m ai_engine.app
    ```

2.  **Enter a topic** when prompted.

3.  The summaries will be saved in a JSON file in the root of the `PGAI` directory.

### Server

The server is a FastAPI application that can generate an image with the summarized content of an article.

1.  **Start the server:**
    ```bash
    uvicorn server.main:app --reload
    ```

2.  **Send a POST request** to the `/content` endpoint with the following JSON payload:
    ```json
    {
      "title": "Your Title",
      "content": "Your one-line summary.",
      "reference": "your.source.com"
    }
    ```

3.  The generated image will be saved as `processed_image.png` in the `server/output` directory.

## Dependencies

The main dependencies are listed in `pyproject.toml` and `requirements.txt`. They include:

- **FastAPI**: For the web server.
- **LangChain & LangGraph**: For building the AI workflow.
- **Pillow & OpenCV**: For image manipulation.
- **Beautiful Soup & Requests**: For web crawling.
- **Pydantic**: For data validation.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature`).
6.  Open a pull request.

## License

This project is licensed under the MIT License.

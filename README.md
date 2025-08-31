# pgai - Post Generator Agent

`pgai` is a FastAPI-based image generation service that creates social media posts by overlaying text onto a base image. It's designed to automate the creation of simple, text-based visual content.

## Features

* **Text-to-Image Generation:** Creates images with a title, content, and reference text.
* **Customizable Text:** The position, size, and content of the text are configurable.
* **FastAPI Backend:** Provides a simple and fast API for generating images.
* **Workflow Automation:** Uses `langgraph` to define a clear and repeatable image processing workflow.
* **Easy to Use:** A single API endpoint to generate images.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/pgai.git
   cd pgai
   ```

2. **Install dependencies with uv:**

   ```bash
   pip install uv
   uv sync
   ```

   This will create a `.venv/` folder and install all dependencies listed in `pyproject.toml`.

## Usage

1. **Run the server:**

   ```bash
   uvicorn server.main:app --reload
   ```

   The server will be running at `http://localhost:8000`.

2. **Send a request to the API:**
   Use `curl`, Postman, or any API client to send a POST request to the `/content` endpoint.

## API Endpoint

### `POST /content`

This endpoint generates an image with the provided text.

**Request Body:**

* `title` (string, required): The title of the post (max 12 characters).
* `content` (string, required): The main content of the post (max 150 characters).
* `reference` (string, required): The reference or source of the content (max 30 characters).

**Example Request:**

```json
{
  "title": "New Post",
  "content": "This is the content of the new post. It can be a quote, a thought, or anything you want to share.",
  "reference": "Reference/Source"
}
```

**Example with `curl`:**

```bash
curl -X POST "http://localhost:8000/content" -H "Content-Type: application/json" -d '{
  "title": "New Post",
  "content": "This is the content of the new post. It can be a quote, a thought, or anything you want to share.",
  "reference": "Reference/Source"
}'
```

**Success Response:**

```json
{
  "message": "Success",
  "Item": {
    "content": "This is the content of the new post. It can be a quote, a thought, or anything you want to share.",
    "reference": "Reference/Source",
    "title": "New Post"
  }
}
```

The generated image will be saved in the `server/output/` directory.

## Project Structure

```
/home/akakathir/Ghost/PGAI/
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── uv.lock
├── __pycache__/
├── .git/...
├── .venv/...
└── server/
    ├── main.py
    ├── workflow.py
    ├── assets/
    │   ├── base.png
    │   ├── glyphnames.json
    │   └── JetBrainsMonoNerdFontMono-BoldItalic.ttf
    └── output/
        └── processed_image.png
```

---

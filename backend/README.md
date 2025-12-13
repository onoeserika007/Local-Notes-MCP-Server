# AI Notes Backend

FastAPI backend for AI-powered note-taking application.

## Features

- ✅ RESTful API for note management (CRUD)
- ✅ SQLite database with SQLAlchemy ORM
- ✅ Async support with aiosqlite
- ✅ Request/Response validation with Pydantic
- ✅ Auto-generated API documentation (Swagger UI)
- 🚧 AI integration with Qwen API (Week 2)
- 🚧 Vector search with ChromaDB (Week 6)

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: SQLite + SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Python**: 3.11+

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Development Server

```bash
# From backend directory
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Notes

- `POST /api/notes` - Create a new note
- `GET /api/notes` - List all notes (with pagination)
- `GET /api/notes/{id}` - Get a specific note
- `PUT /api/notes/{id}` - Update a note
- `DELETE /api/notes/{id}` - Delete a note

### Query Parameters

- `page` - Page number (default: 1)
- `limit` - Items per page (default: 10, max: 100)
- `tag` - Filter by tag
- `search` - Search in title and content

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration management
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── note.py          # SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── note.py          # Pydantic schemas
│   └── api/
│       └── routes/
│           ├── __init__.py
│           └── notes.py     # Notes API routes
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
# Install dev dependencies
pip install black isort flake8

# Format code
black app/
isort app/

# Check style
flake8 app/
```

## Database

SQLite database file: `notes.db` (created automatically on first run)

### Schema

**notes** table:
- `id` - Primary key
- `title` - Note title (max 255 chars)
- `content` - Note content (Markdown)
- `tags` - JSON array of tags
- `summary` - AI-generated summary (optional)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## Testing with curl

```bash
# Create a note
curl -X POST "http://localhost:8000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Note",
    "content": "# Hello World\n\nThis is my first note.",
    "tags": ["test", "hello"]
  }'

# List notes
curl "http://localhost:8000/api/notes?page=1&limit=10"

# Get a specific note
curl "http://localhost:8000/api/notes/1"

# Update a note
curl -X PUT "http://localhost:8000/api/notes/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "content": "Updated content"
  }'

# Delete a note
curl -X DELETE "http://localhost:8000/api/notes/1"
```

## Next Steps (Week 2)

- [ ] Integrate Qwen API for AI features
- [ ] Add `/api/ai/summarize` endpoint
- [ ] Add `/api/ai/chat` endpoint
- [ ] Implement error handling and logging
- [ ] Add unit tests

## License

MIT

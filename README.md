# Rekindled

Rekindled transforms your e-reader highlights into beautifully formatted Memory Reports — genre-aware, AI-generated summaries of your personal highlights from each book.

## What it does

- Upload your Kindle `My Clippings.txt` file
- Select a book from your library
- Choose your preferred language
- Get a beautifully formatted PDF Memory Report powered by Claude

## Genres supported

Science, History & Politics, Economics & Finance, Technology & AI, Personal Growth & Self-Help, Philosophy & Spirituality, Literary Fiction, Science Fiction & Fantasy, Biography & Memoir, Poetry & Essays

## Languages supported

English, Turkish, Spanish, French, Italian, German, Portuguese

## How to run locally

1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your Anthropic API key: `ANTHROPIC_API_KEY=your_key_here`
5. Run the app: `python app.py`
6. Open `http://127.0.0.1:5001` in your browser

## Built with

- Python / Flask
- Claude API (Haiku for genre detection, Opus for report generation)
- ReportLab for PDF generation
- Inter font

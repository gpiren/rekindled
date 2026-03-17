import anthropic
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open("highlights.json", "r", encoding="utf-8") as f:
    books = json.load(f)

print("Available books:")
for i, title in enumerate(books.keys(), 1):
    print(f"{i}. {title}")

choice = input("\nEnter the number of the book you want to summarise: ")
title = list(books.keys())[int(choice) - 1]
highlights = books[title]
highlights_text = "\n".join([f"- {h}" for h in highlights])
sample_highlights = "\n".join([f"- {h}" for h in highlights[:3]])

print("\nAvailable languages:")
languages = [
    "English",
    "Turkish",
    "Spanish",
    "French",
    "Italian",
    "German",
    "Portuguese",
]
for i, lang in enumerate(languages, 1):
    print(f"{i}. {lang}")

lang_choice = input("\nEnter the number of the language for your report: ")
report_language = languages[int(lang_choice) - 1]
print(f"\nReport language: {report_language}")

genre_message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=20,
    messages=[
        {"role": "user", "content": f"""Given this book title and sample highlights, classify it into exactly one of these genres:
Science, History & Politics, Economics & Finance, Technology & AI, Personal Growth & Self-Help, Philosophy & Spirituality, Literary Fiction, Science Fiction & Fantasy, Biography & Memoir, Poetry & Essays

Book title: {title}
Sample highlights:
{sample_highlights}

Reply with only the genre name, nothing else."""}
    ]
)

genre = genre_message.content[0].text.strip()
print(f"\nDetected genre: {genre}")

prompts = {
    "Science": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key terms or concepts when they first appear. Focus on explaining the core concepts and mechanisms clearly. Where helpful, briefly clarify technical terms in plain language. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "History & Politics": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key terms, figures or events when they first appear. Synthesise the key events, arguments and ideas into a coherent narrative. Where useful, briefly mention real historical context or examples to support the ideas. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Economics & Finance": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key terms or concepts when they first appear. Explain the key concepts and arguments clearly. Where helpful, use brief real-world examples or historical context to illustrate ideas without overwhelming the reader. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Technology & AI": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key terms or concepts when they first appear. Focus on the key ideas and their practical implications. Explain technical concepts accessibly. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Personal Growth & Self-Help": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key principles or ideas when they first appear. Focus on the actionable insights and core principles. Keep the tone direct, practical and motivating. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Philosophy & Spirituality": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key concepts or thinkers when they first appear. Explore the ideas with depth and intellectual curiosity. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Literary Fiction": f"""Here are my highlights from '{title}':

{highlights_text}

Return each highlight exactly as it appears, one by one. Do not add any commentary, summary or explanation. Just the highlights themselves.""",

    "Science Fiction & Fantasy": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key concepts, characters or world-building terms when they first appear. Note the world-building, thematic, and character elements that made these passages worth highlighting. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Biography & Memoir": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** for key names, turning points or ideas when they first appear. Capture the narrative arc of the person's life and ideas as reflected in these passages. Scale the length of the report to the number of highlights — do not pad or over-explain. Write the entire report in {report_language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone.""",

    "Poetry & Essays": f"""Here are my highlights from '{title}':

{highlights_text}

Write a Memory Report on these highlights. Use ## subheadings to organise the report into thematic sections. Use **bold** sparingly for particularly resonant phrases or ideas. Preserve the highlights as they are and add light annotations on tone, feeling and resonance. Do not over-analyse. Keep it short. Write the entire report in {report_language}. No bullet points, no em dashes.""",
}

prompt = prompts.get(genre, prompts["History & Politics"])

report_message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print(f"\n{report_message.content[0].text}")

##############################################

# Saving the report

report_data = {
    "book_title": title,
    "genre": genre,
    "highlight_count": len(highlights),
    "date_generated": datetime.now().strftime("%B %d, %Y"),
    "report_language": report_language,
    "report_text": report_message.content[0].text
}

with open("report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)

print("\nReport saved to report.json")


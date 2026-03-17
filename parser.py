import json

with open("My Clippings.txt", "r", encoding="utf-8") as f:
    content = f.read()

entries = content.split("==========")

books = {}
for entry in entries:
    lines = entry.strip().split("\n")
    if len(lines) < 3:
        continue
    title = lines[0].strip()
    highlight = lines[-1].strip()
    if "clipping limit" in highlight.lower():
        continue
    if title not in books:
        books[title] = []
    books[title].append(highlight)

with open("highlights.json", "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print("Saved successfully.")
for title, highlights in books.items():
    print(f"{title}: {len(highlights)} highlights")
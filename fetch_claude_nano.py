import anthropic
import os
from datetime import datetime

# Načtení API klíče z prostředí GitHub Actions
client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# Načtení systémových instrukcí a uživatelského promptu ze souborů
with open("sys_instr_nano.txt", "r", encoding="utf-8") as f:
    system_instructions = f.read()

with open("user_prompt_nano.txt", "r", encoding="utf-8") as f:
    user_prompt = f.read()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=system_instructions,
    messages=[{"role": "user", "content": user_prompt}]
)

content = response.content[0].text
date_str = datetime.now().strftime("%Y-%m-%d")

# Vytvoření složky pro příspěvky, pokud neexistuje
os.makedirs("_posts", exist_ok=True)

# Uložení do souboru s hlavičkou pro web (Jekyll front matter)
filename = f"_posts/{date_str}-post.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\nlayout: post\ntitle: 'Zápis pro {date_str}'\ndate: {date_str}\n---\n\n")
    f.write(content)

print(f"Příspěvek {filename} byl úspěšně vytvořen.")

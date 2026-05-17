import anthropic
import os
from datetime import datetime

# Načtení API klíče z prostředí GitHub Actions
client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# Načtení systémových instrukcí a uživatelského promptu ze souborů
with open("sys_instr_geo1.txt", "r", encoding="utf-8") as f:
    system_instructions = f.read()

with open("user_prompt_geo1.txt", "r", encoding="utf-8") as f:
    user_prompt = f.read()

response = client.messages.create(
### model="claude-haiku-4-5-20251001", 
    model="claude-opus-4-7",
    max_tokens=8192,
    system=system_instructions,
### Pozor, nejedu-li na OPUSu, zakomentovat i "tools" parametr !
    tools=[
            {
            "type": "web_search_20260209",
            "name": "web_search"
            }
          ],
    messages=[{"role": "user", "content": user_prompt}]
)

# content = response.content[0].text
content = "\n".join(
    block.text for block in response.content if block.type == "text"
)

date_str = datetime.now().strftime("%Y-%m-%d")

# Vytvoření složky pro příspěvky, pokud neexistuje
os.makedirs("_posts", exist_ok=True)

# Uložení do souboru s hlavičkou pro web (Jekyll front matter)
filename = f"_posts/{date_str}-post.md"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"---\nlayout: post\ntitle: 'Zápis pro {date_str}'\ndate: {date_str}\n---\n\n")
    f.write(content)

print(f"Příspěvek {filename} byl úspěšně vytvořen.")

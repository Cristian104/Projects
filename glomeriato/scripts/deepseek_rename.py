import os
import json
import urllib.request
import re
from pathlib import Path

NOTES_DIR = "/home/jorg/stacks/remastered_bot/notebook/Research_Notes"
MODEL = "deepseek-r1:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

def ask_deepseek(prompt):
    payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 4096}}
    try:
        req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8')).get("response", "")
    except Exception as e:
        return ""

def rename_files():
    notes_dir = Path(NOTES_DIR)
    md_files = list(notes_dir.rglob("*.md"))
    
    print(f"Found {len(md_files)} files. Starting DeepSeek naming process...")
    
    for md_file in md_files:
        # Only rename files that look like raw IDs (contain numbers or 'ssrn')
        if not re.search(r'\d{4,}', md_file.stem):
            continue
            
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Grab first 500 words for accurate context
        words = content.split()
        sample_text = " ".join(words[:500])
        
        prompt = (
            "You are a helpful assistant. Read this excerpt from a research paper.\n"
            "Create a short, descriptive filename for this paper (maximum 5 words).\n"
            "Format it in snake_case (e.g., 'financial_agentic_workflows').\n"
            "Output strictly ONLY the snake_case name. No explanations.\n\n"
            f"Excerpt:\n{sample_text}"
        )
        
        print(f"[+] Generating name for: {md_file.name}")
        raw_res = ask_deepseek(prompt)
        
        # Strip out DeepSeek's <think> blocks
        clean_res = re.sub(r'<think>.*?</think>', '', raw_res, flags=re.DOTALL).strip()
        
        # Extract the snake_case string
        match = re.search(r'([a-zA-Z0-9_]{5,})', clean_res)
        if not match:
            print("    ! Failed to get a valid name. Skipping.")
            continue
            
        clean_name = match.group(1).lower().strip('_')
        
        if clean_name == md_file.stem:
            continue
            
        new_md_path = md_file.parent / f"{clean_name}.md"
        old_stem = md_file.stem
        old_assets_dir = md_file.parent / f"{old_stem}_assets"
        new_assets_dir = md_file.parent / f"{clean_name}_assets"
        
        print(f"    -> Renamed to: {clean_name}.md")
        
        # 1. Rename the assets folder
        if old_assets_dir.exists():
            os.rename(old_assets_dir, new_assets_dir)
            
        # 2. Update image links inside the Markdown
        content = content.replace(f"{old_stem}_assets/", f"{clean_name}_assets/")
        
        # 3. Save new file and delete old
        with open(new_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        if new_md_path != md_file:
            md_file.unlink()

if __name__ == "__main__":
    rename_files()

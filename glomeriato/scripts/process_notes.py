import os
import json
import urllib.request
import re
from pathlib import Path

NOTES_DIR = "/home/jorg/stacks/remastered_bot/notebook/Research_Notes"
MODEL = "deepseek-r1:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

class ResearchProcessor:
    def __init__(self):
        self.notes_dir = Path(NOTES_DIR)

    def ask_deepseek(self, prompt):
        payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 4096}}
        try:
            req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode('utf-8'))
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8')).get("response", "")
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_filename(self, content):
        """Passes the first 500 words to DeepSeek to generate a clean snake_case filename."""
        words = content.split()
        sample = " ".join(words[:500])
        prompt = (
            "You are a helpful assistant. Read this excerpt from a research paper.\n"
            "Create a short, descriptive filename for this paper (maximum 5 words).\n"
            "Format it strictly in snake_case (e.g., 'financial_ai_agents').\n"
            "Output strictly ONLY the snake_case name. No explanations.\n\n"
            f"Excerpt:\n{sample}"
        )
        raw_res = self.ask_deepseek(prompt)
        clean_res = re.sub(r'<think>.*?</think>', '', raw_res, flags=re.DOTALL).strip()
        match = re.search(r'([a-zA-Z0-9_]{5,})', clean_res)
        return match.group(1).lower().strip('_') if match else None

    def process_files(self):
        print(f"--- Analyzing with {MODEL} ---")
        files = list(self.notes_dir.rglob("*.md"))
        
        for md_file in files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if already processed (has YAML header)
            if content.startswith("---"): 
                continue

            cat = "general"
            if "brain" in str(md_file).lower(): cat = "brain"
            elif "guardian" in str(md_file).lower(): cat = "guardian"
            elif "sentinel" in str(md_file).lower(): cat = "sentinel"

            print(f"[+] Processing: {md_file.name}")
            
            # 1. Generate the Summary
            summary_prompt = f"Summarize this research for Obsidian. Tags: #research #{cat}. Content: {content[:4000]}"
            raw_summary = self.ask_deepseek(summary_prompt)
            clean_summary = re.sub(r'<think>.*?</think>', '', raw_summary, flags=re.DOTALL).strip()
            
            # 2. Generate the Filename
            new_name = self.get_filename(content)
            clean_name = new_name if new_name else md_file.stem

            # 3. Path Mapping & Folder Renaming
            new_md_name = f"{clean_name}.md"
            new_md_path = md_file.parent / new_md_name
            
            old_stem = md_file.stem
            old_assets_dir = md_file.parent / f"{old_stem}_assets"
            new_assets_dir = md_file.parent / f"{clean_name}_assets"

            if old_assets_dir.exists() and clean_name != old_stem:
                os.rename(old_assets_dir, new_assets_dir)
            
            if clean_name != old_stem:
                content = content.replace(f"{old_stem}_assets/", f"{clean_name}_assets/")

            # 4. Construct Final Document
            yaml_header = f"---\ncategory: {cat}\ntags: [research, {cat}]\n---\n\n"
            
            with open(new_md_path, 'w', encoding='utf-8') as f:
                f.write(f"{yaml_header}{clean_summary}\n\n---\n\n{content}")
            
            if new_md_path != md_file:
                md_file.unlink()
                
            print(f"   ✓ Saved as {new_md_name}")

if __name__ == "__main__":
    ResearchProcessor().process_files()

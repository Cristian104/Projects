#!/usr/bin/env python3
import urllib.request
import json
import subprocess
import os
import sys

def main():
    url = "http://localhost:8009/api/articles"
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching articles: {e}")
        sys.exit(1)

    top_articles = [a for a in data if a.get("rank_overall") and a["rank_overall"] <= 5]
    top_articles.sort(key=lambda x: x["rank_overall"])

    if not top_articles:
        print("No top articles found.")
        sys.exit(0)

    lines = ["🌐 *Daily Top 5 Tech Briefing* (`news.mybrain.world`)\n"]
    for i, a in enumerate(top_articles, 1):
        title = a.get("title", "").strip()
        link = a.get("link", "#")
        source = a.get("source", "Tech")
        summary = a.get("ai_summary", a.get("summary", "")).strip()
        # Keep top 2 bullet points for conciseness
        summary_lines = [l.strip() for l in summary.split("\n") if l.strip()][:2]
        clean_summary = "\n".join(summary_lines)
        impact = a.get("ai_impact_reason", "").strip()

        lines.append(f"*{i}. [{title}]({link})*")
        lines.append(f"📍 _{source}_")
        if clean_summary:
            lines.append(f"{clean_summary}")
        if impact:
            lines.append(f"💡 *Impact:* _{impact}_\n")
        else:
            lines.append("")

    digest_body = "\n".join(lines)
    prompt = (
        "Send this Daily Tech Briefing to the user on Telegram. "
        "Keep it in ONE single message without splitting, using exact Markdown formatting:\n\n"
        f"{digest_body}"
    )

    openclaw_bin = "/home/jorg/.nvm/versions/node/v24.21.0/bin/openclaw"
    cmd = [
        openclaw_bin, "agent",
        "--agent", "main",
        "--deliver",
        "--reply-channel", "telegram",
        "--reply-to", "7585332236",
        "-m", prompt
    ]
    
    env = dict(os.environ)
    env["PATH"] = "/home/jorg/.nvm/versions/node/v24.21.0/bin:" + env.get("PATH", "")
    env["OPENCLAW_GATEWAY_TOKEN"] = "839f89a481ec25ad98808be2c0f60ad50f8382aef481006aa8c9133ddf9b0dde"
    
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)

if __name__ == "__main__":
    main()

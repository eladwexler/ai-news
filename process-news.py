import os
import sys
from datetime import datetime
import json
import textwrap
import html 

PILLARS = {
    "macro_finance": [
        "capex", "capital expenditure", "hyperscaler", "free cash flow", 
        "operating margins", "depreciation schedule"
    ],
    "silicon_hardware": [
        "gpu", "tpu", "asic", "accelerator", "hbm", "inference", "training workload"
    ],
    "supply_chain_chokepoints": [
        "advanced packaging", "cowos", "tsmc", "foundry", "yield rate", "lead time"
    ],
    "physical_infrastructure": [
        "data center", "power grid", "electricity", "transformer", "liquid cooling", "megawatt"
    ],
    "robotics": [
        "robot", "robotics", "humanoid", "embodied ai", "physical ai", "actuator",
        "manipulation", "warehouse automation", "autonomous mobile"
    ],
    "quantum_computing": [
        "quantum", "qubit", "qpu", "superconducting qubit", "trapped ion",
        "quantum error correction", "quantum annealing", "quantum supremacy"
    ]
}

def analyze_article_relevance(content):
    content_lower = content.lower()
    matched_tags = []
    for pillar, keywords in PILLARS.items():
        if any(keyword in content_lower for keyword in keywords):
            matched_tags.append(pillar)
    return matched_tags

def process_daily_folder(target_dir):
    if not os.path.exists(target_dir):
        print(f"[Error] Directory '{target_dir}' does not exist.")
        return

    print(f"Processing articles in folder: {target_dir}\n")
    
    llm_payload = []
    skipped_count = 0

    for filename in os.listdir(target_dir):
        if not filename.endswith('.txt') or filename in ["human-readable.txt", "optimized_llm_payload.json"]:
            continue
            
        filepath = os.path.join(target_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if len(lines) < 6:
                continue 
                
            source = lines[0].replace("SOURCE:", "").strip()
            title = lines[1].replace("TITLE:", "").strip()
            date = lines[2].replace("DATE:", "").strip()
            url = lines[3].replace("URL:", "").strip()
            
            content_body = "".join(lines[6:])
            content_body = html.unescape(content_body)
            
            title = html.unescape(title)
            source = html.unescape(source)
            
            matched_pillars = analyze_article_relevance(content_body)
            
            if not matched_pillars:
                skipped_count += 1
                continue
                
            truncated_content = content_body[:3000].strip()
            if len(content_body) > 3000:
                truncated_content += "... [TRUNCATED]"

            llm_payload.append({
                "title": title,
                "source": source,
                "date": date,
                "url": url,
                "tags": matched_pillars,
                "content": truncated_content
            })
        except Exception as e:
            print(f"  [Warning] Failed to read {filename}: {e}")

    print(f"Filtering Complete:")
    print(f"  - High-signal articles retained: {len(llm_payload)}")
    print(f"  - Irrelevant articles dropped: {skipped_count}\n")

    # --- OUTPUT 1: JSON Data ---
    output_json_path = os.path.join(target_dir, "optimized_llm_payload.json")
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(llm_payload, json_file, indent=2)
    print(f"[Success] Saved optimized LLM payload to: {output_json_path}")

    # --- OUTPUT 2: Human Readable Text File (Strictly Max 80 Chars per Line) ---
    output_txt_path = os.path.join(target_dir, "human-readable.txt")
    
    # 80 max character limit minus a 6-character left indent margin (width=74)
    wrapper = textwrap.TextWrapper(width=74, break_long_words=False, replace_whitespace=False)

    with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
        # Multipliers dynamically generate exactly 80 characters of dividers
        txt_file.write(f"{'=' * 80}\n")
        txt_file.write(f"   DAILY INTELLIGENCE DIGEST: {os.path.basename(target_dir)}\n")
        txt_file.write(f"{'=' * 80}\n\n")
        txt_file.write(f"Total High-Signal Articles Filtered: {len(llm_payload)}\n")
        txt_file.write(f"Irrelevant Feed Items Dropped: {skipped_count}\n")
        txt_file.write(f"{'-' * 80}\n\n")
        
        for idx, item in enumerate(llm_payload, 1):
            tags_str = ", ".join([t.upper().replace('_', ' ') for t in item['tags']])
            
            txt_file.write(f"{idx}. TITLE: {item['title']}\n")
            txt_file.write(f"   SOURCE: {item['source']} | DATE: {item['date']}\n")
            txt_file.write(f"   URL: {item['url']}\n")
            txt_file.write(f"   MATCHED PILLARS: [{tags_str}]\n")
            txt_file.write(f"   EXTRACTED SNIPPET:\n")
            
            paragraphs = item['content'].split('\n')
            for para in paragraphs:
                if not para.strip():
                    continue
                wrapped_lines = wrapper.wrap(para)
                for w_line in wrapped_lines:
                    txt_file.write(f"      {w_line}\n")
                    
            txt_file.write(f"\n{'-' * 80}\n\n")
            
    print(f"[Success] Saved human readable log to: {output_txt_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        chosen_dir = sys.argv[1]
    else:
        today_str = datetime.today().strftime('%Y-%m-%d')
        chosen_dir = os.path.join(os.getcwd(), today_str)
        print(f"No path specified. Defaulting to today's folder.")

    process_daily_folder(chosen_dir)

# /run-news — Fetch, Process, and Analyze AI News for Stock Ideas

Run the full news pipeline for **today only**, then analyze the output and surface interesting stock ideas.

## Steps

**1. Determine today's folder**

Today's date folder is `/home/ewexler/projects/ai-news/<YYYY-MM-DD>` where the date is today's date.
Compute it with:

```bash
python3 -c "from datetime import datetime; print(datetime.today().strftime('%Y-%m-%d'))"
```

Use the printed value as `<TODAY>` in all subsequent steps.

**2. Fetch today's news only**

```bash
cd /home/ewexler/projects/ai-news && python3 news-today.py
```

This script filters to articles published in the last 24 hours and saves them into `/home/ewexler/projects/ai-news/<TODAY>/`.

**3. Process into LLM-ready payload**

```bash
cd /home/ewexler/projects/ai-news && python3 process-news.py /home/ewexler/projects/ai-news/<TODAY>
```

This reads only the articles in today's folder and writes `optimized_llm_payload.json` and `human-readable.txt` into the same folder.

**4. Read the output**

Read `/home/ewexler/projects/ai-news/<TODAY>/optimized_llm_payload.json`.

**5. Analyze and surface stock ideas**

Read every article in the JSON payload. For each article, extract:
- Companies explicitly named
- Technology or infrastructure trends with investable implications
- Supply chain developments, capacity announcements, or contract wins/losses
- Regulatory or geopolitical signals that affect specific sectors

Then produce a **Stock Ideas Table** with this exact structure:

```
## Stock Ideas — <TODAY>

| Ticker | Company | Direction | Thesis (1-2 sentences) | Time Horizon | Pillar |
|--------|---------|-----------|------------------------|--------------|--------|
| NVDA   | Nvidia  | Bullish   | ...                    | 3-6 months   | silicon_hardware |
```

Rules for the analysis:
- Only include tickers for publicly traded companies (NYSE/NASDAQ). Skip private companies.
- Direction must be Bullish, Bearish, or Neutral/Watch.
- Thesis must be grounded in a specific fact from the articles, not general sentiment.
- Time Horizon: Near-term (1-4 weeks), Medium (1-6 months), or Long (6 months+).
- Pillar: one of macro_finance | silicon_hardware | supply_chain_chokepoints | physical_infrastructure.
- After the table, add a **Key Risks** bullet list per idea where the thesis could be wrong.
- End with a **Top Pick** section: one sentence naming the single most interesting idea and why.

**6. Write the analysis to disk**

Write the full analysis (Stock Ideas Table, Key Risks, Top Pick) to:

```
/home/ewexler/projects/ai-news/<TODAY>/stock-analysis.md
```

Use the Write tool with that exact path. Do not truncate or summarize the output.

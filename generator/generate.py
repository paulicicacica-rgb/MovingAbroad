#!/usr/bin/env python3
"""
MoveGuide Page Generator
Usage:
  python3 generate.py           # full run
  python3 generate.py --test    # test mode (5 pages only)
  python3 generate.py --dest ireland  # only one destination
"""

import os, sys, re, time, requests, argparse
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
BASE_DIR    = SCRIPT_DIR.parent
PUBLIC_DIR  = BASE_DIR / "public"
LOG_FILE    = SCRIPT_DIR / "progress.log"
ENV_FILE    = BASE_DIR / ".env"

# ── Load .env manually (no dependency on dotenv) ──────────────────────────────
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
UNSPLASH_KEY   = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# ── Countries ─────────────────────────────────────────────────────────────────
DESTINATIONS = [
    {"code":"ireland",       "name":"Ireland",        "capital":"Dublin",        "currency":"EUR","emoji":"🇮🇪"},
    {"code":"united-kingdom","name":"United Kingdom",  "capital":"London",        "currency":"GBP","emoji":"🇬🇧"},
    {"code":"canada",        "name":"Canada",          "capital":"Toronto",       "currency":"CAD","emoji":"🇨🇦"},
    {"code":"australia",     "name":"Australia",       "capital":"Sydney",        "currency":"AUD","emoji":"🇦🇺"},
    {"code":"usa",           "name":"United States",   "capital":"New York",      "currency":"USD","emoji":"🇺🇸"},
    {"code":"germany",       "name":"Germany",         "capital":"Berlin",        "currency":"EUR","emoji":"🇩🇪"},
    {"code":"netherlands",   "name":"Netherlands",     "capital":"Amsterdam",     "currency":"EUR","emoji":"🇳🇱"},
    {"code":"uae",           "name":"UAE",             "capital":"Dubai",         "currency":"AED","emoji":"🇦🇪"},
    {"code":"new-zealand",   "name":"New Zealand",     "capital":"Auckland",      "currency":"NZD","emoji":"🇳🇿"},
    {"code":"singapore",     "name":"Singapore",       "capital":"Singapore",     "currency":"SGD","emoji":"🇸🇬"},
    {"code":"portugal",      "name":"Portugal",        "capital":"Lisbon",        "currency":"EUR","emoji":"🇵🇹"},
    {"code":"spain",         "name":"Spain",           "capital":"Madrid",        "currency":"EUR","emoji":"🇪🇸"},
    {"code":"switzerland",   "name":"Switzerland",     "capital":"Zurich",        "currency":"CHF","emoji":"🇨🇭"},
    {"code":"sweden",        "name":"Sweden",          "capital":"Stockholm",     "currency":"SEK","emoji":"🇸🇪"},
    {"code":"norway",        "name":"Norway",          "capital":"Oslo",          "currency":"NOK","emoji":"🇳🇴"},
    {"code":"france",        "name":"France",          "capital":"Paris",         "currency":"EUR","emoji":"🇫🇷"},
    {"code":"japan",         "name":"Japan",           "capital":"Tokyo",         "currency":"JPY","emoji":"🇯🇵"},
    {"code":"malaysia",      "name":"Malaysia",        "capital":"Kuala Lumpur",  "currency":"MYR","emoji":"🇲🇾"},
    {"code":"south-africa",  "name":"South Africa",    "capital":"Cape Town",     "currency":"ZAR","emoji":"🇿🇦"},
    {"code":"brazil",        "name":"Brazil",          "capital":"Sao Paulo",     "currency":"BRL","emoji":"🇧🇷"},
]

ORIGINS = [
    {"code":"romania",        "name":"Romania",           "emoji":"🇷🇴"},
    {"code":"poland",         "name":"Poland",            "emoji":"🇵🇱"},
    {"code":"italy",          "name":"Italy",             "emoji":"🇮🇹"},
    {"code":"portugal",       "name":"Portugal",          "emoji":"🇵🇹"},
    {"code":"france",         "name":"France",            "emoji":"🇫🇷"},
    {"code":"germany",        "name":"Germany",           "emoji":"🇩🇪"},
    {"code":"spain",          "name":"Spain",             "emoji":"🇪🇸"},
    {"code":"ukraine",        "name":"Ukraine",           "emoji":"🇺🇦"},
    {"code":"greece",         "name":"Greece",            "emoji":"🇬🇷"},
    {"code":"hungary",        "name":"Hungary",           "emoji":"🇭🇺"},
    {"code":"bulgaria",       "name":"Bulgaria",          "emoji":"🇧🇬"},
    {"code":"serbia",         "name":"Serbia",            "emoji":"🇷🇸"},
    {"code":"croatia",        "name":"Croatia",           "emoji":"🇭🇷"},
    {"code":"slovakia",       "name":"Slovakia",          "emoji":"🇸🇰"},
    {"code":"czech-republic", "name":"Czech Republic",    "emoji":"🇨🇿"},
    {"code":"india",          "name":"India",             "emoji":"🇮🇳"},
    {"code":"philippines",    "name":"Philippines",       "emoji":"🇵🇭"},
    {"code":"pakistan",       "name":"Pakistan",          "emoji":"🇵🇰"},
    {"code":"bangladesh",     "name":"Bangladesh",        "emoji":"🇧🇩"},
    {"code":"sri-lanka",      "name":"Sri Lanka",         "emoji":"🇱🇰"},
    {"code":"nepal",          "name":"Nepal",             "emoji":"🇳🇵"},
    {"code":"china",          "name":"China",             "emoji":"🇨🇳"},
    {"code":"indonesia",      "name":"Indonesia",         "emoji":"🇮🇩"},
    {"code":"malaysia",       "name":"Malaysia",          "emoji":"🇲🇾"},
    {"code":"singapore",      "name":"Singapore",         "emoji":"🇸🇬"},
    {"code":"vietnam",        "name":"Vietnam",           "emoji":"🇻🇳"},
    {"code":"thailand",       "name":"Thailand",          "emoji":"🇹🇭"},
    {"code":"japan",          "name":"Japan",             "emoji":"🇯🇵"},
    {"code":"south-korea",    "name":"South Korea",       "emoji":"🇰🇷"},
    {"code":"iran",           "name":"Iran",              "emoji":"🇮🇷"},
    {"code":"iraq",           "name":"Iraq",              "emoji":"🇮🇶"},
    {"code":"syria",          "name":"Syria",             "emoji":"🇸🇾"},
    {"code":"lebanon",        "name":"Lebanon",           "emoji":"🇱🇧"},
    {"code":"jordan",         "name":"Jordan",            "emoji":"🇯🇴"},
    {"code":"kazakhstan",     "name":"Kazakhstan",        "emoji":"🇰🇿"},
    {"code":"nigeria",        "name":"Nigeria",           "emoji":"🇳🇬"},
    {"code":"ghana",          "name":"Ghana",             "emoji":"🇬🇭"},
    {"code":"kenya",          "name":"Kenya",             "emoji":"🇰🇪"},
    {"code":"south-africa",   "name":"South Africa",      "emoji":"🇿🇦"},
    {"code":"ethiopia",       "name":"Ethiopia",          "emoji":"🇪🇹"},
    {"code":"tanzania",       "name":"Tanzania",          "emoji":"🇹🇿"},
    {"code":"uganda",         "name":"Uganda",            "emoji":"🇺🇬"},
    {"code":"senegal",        "name":"Senegal",           "emoji":"🇸🇳"},
    {"code":"cameroon",       "name":"Cameroon",          "emoji":"🇨🇲"},
    {"code":"morocco",        "name":"Morocco",           "emoji":"🇲🇦"},
    {"code":"usa",            "name":"United States",     "emoji":"🇺🇸"},
    {"code":"canada",         "name":"Canada",            "emoji":"🇨🇦"},
    {"code":"mexico",         "name":"Mexico",            "emoji":"🇲🇽"},
    {"code":"brazil",         "name":"Brazil",            "emoji":"🇧🇷"},
    {"code":"colombia",       "name":"Colombia",          "emoji":"🇨🇴"},
    {"code":"venezuela",      "name":"Venezuela",         "emoji":"🇻🇪"},
    {"code":"argentina",      "name":"Argentina",         "emoji":"🇦🇷"},
    {"code":"jamaica",        "name":"Jamaica",           "emoji":"🇯🇲"},
    {"code":"trinidad",       "name":"Trinidad and Tobago","emoji":"🇹🇹"},
    {"code":"peru",           "name":"Peru",              "emoji":"🇵🇪"},
    {"code":"australia",      "name":"Australia",         "emoji":"🇦🇺"},
    {"code":"new-zealand",    "name":"New Zealand",       "emoji":"🇳🇿"},
    {"code":"ireland",        "name":"Ireland",           "emoji":"🇮🇪"},
    {"code":"united-kingdom", "name":"United Kingdom",    "emoji":"🇬🇧"},
    {"code":"fiji",           "name":"Fiji",              "emoji":"🇫🇯"},
]

# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Unsplash ──────────────────────────────────────────────────────────────────
def get_image(query):
    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=10
        )
        data = r.json()
        if data.get("results"):
            p = data["results"][0]
            return {
                "url":               p["urls"]["regular"],
                "photographer":      p["user"]["name"],
                "photographer_url":  p["user"]["links"]["html"],
            }
    except Exception as e:
        log(f"  ⚠️  Unsplash: {e}")
    return None

# ── Claude ────────────────────────────────────────────────────────────────────
def generate_content(origin, destination):
    ON = origin["name"]
    DN = destination["name"]
    DC = destination["capital"]

    prompt = f"""You are writing a detailed practical relocation guide for people moving from {ON} to {DN}.
Be specific, honest, use real numbers. Like a knowledgeable friend. Plain English reading level 10.
Each section must be 150-200 words. Rich, detailed, genuinely useful.

Write each section inside the XML tags exactly as shown:

<verdict>
4-5 honest sentences: is it worth moving from {ON} to {DN}? Quality of life, finances, career, pros AND cons. Specific and real.
</verdict>

<visa>
Detailed visa options for a {ON} citizen moving to {DN}. Work permits with salary thresholds and processing times, family/partner routes, student options, any special bilateral agreements between {ON} and {DN}.
</visa>

<before_you_leave>
8-10 practical things to sort before leaving {ON} for {DN}. Documents to gather, financial prep, what to do with property/car/lease, notifying tax authorities, health insurance gap, first-month budget, job search prep. Full sentences, real detail.
</before_you_leave>

<arrival>
Day-by-day first week in {DN}. Day 1: SIM card, transport card, orientation. Day 2-3: temporary housing strategy, best apartment sites. Day 4-5: register with authorities. Day 6-7: GP registration, local area orientation. Practical detail each step.
</arrival>

<first_month>
5 essential admin tasks first month in {DN}: 1) Local tax/ID number - name, where to go, what to bring, how long. 2) Bank account - best banks for newcomers, requirements. 3) Healthcare - public vs private, costs, how to register. 4) Driving licence transfer - process, timeline, costs. 5) Any {ON}-specific considerations like qualification recognition.
</first_month>

<money>
Monthly budget single person in {DC}. Specific figures for: rent city centre vs suburbs, groceries, utilities, transport monthly pass, phone, eating out, entertainment, health insurance. Total for tight/comfortable/good lifestyle. Sending money back to {ON} - best services and fees.
</money>

<work>
Job market in {DN} for someone from {ON}. Top 5 sectors hiring, average salaries by sector in local currency, qualification recognition from {ON}, language requirements, best job sites, interview culture differences, whether {ON} experience is valued. Realistic after-tax salary expectations.
</work>

<life>
Daily life in {DN} for {ON} expats. Weather reality not just facts, housing market tips and scams to avoid, where people from {ON} tend to live, Facebook groups and community, cultural surprises, finding {ON} food, transport, healthcare quality, overall expat happiness.
</life>

<meta_description>
150-char SEO description for: moving from {ON} to {DN}.
</meta_description>

<hero_intro>
One punchy honest sentence under 20 words summarising what this move is really like.
</hero_intro>"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":          ANTHROPIC_KEY,
                "anthropic-version":  "2023-06-01",
                "content-type":       "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 8000,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        raw = r.json()["content"][0]["text"]

        def x(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
            return m.group(1).strip() if m else ""

        result = {k: x(k) for k in [
            "verdict","visa","before_you_leave","arrival",
            "first_month","money","work","life",
            "meta_description","hero_intro"
        ]}

        if not result["verdict"]:
            log(f"  ❌ Empty content returned")
            return None
        return result

    except Exception as e:
        log(f"  ❌ Claude: {e}")
        return None

# ── HTML ──────────────────────────────────────────────────────────────────────
def to_html(text):
    """Convert newline-separated text to HTML paragraphs or bullet list."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Strip leading numbers/bullets
    cleaned = [re.sub(r"^[\d]+[.)]\s*|^[-•*]\s*", "", l) for l in lines]
    cleaned = [l for l in cleaned if len(l) > 8]
    if len(cleaned) > 2:
        items = "".join(f"<li>{l}</li>" for l in cleaned)
        return f'<ul class="clist">{items}</ul>'
    return "".join(f"<p>{l}</p>" for l in cleaned)

def build_html(origin, dest, content, image):
    ON  = origin["name"];  OE = origin["emoji"];  OC = origin["code"]
    DN  = dest["name"];    DE = dest["emoji"];     DC = dest["code"]
    CAP = dest["capital"]

    img_block = ""
    if image:
        img_block = (
            f'<div class="himg">'
            f'<img src="{image["url"]}" alt="{DN} city" loading="lazy">'
            f'<span class="credit">Photo by '
            f'<a href="{image["photographer_url"]}?utm_source=moveguide&utm_medium=referral" target="_blank">'
            f'{image["photographer"]}</a> on '
            f'<a href="https://unsplash.com?utm_source=moveguide&utm_medium=referral" target="_blank">Unsplash</a>'
            f'</span></div>'
        )

    def sec(num, sid, title, body):
        return (
            f'<section class="sec" id="{sid}">'
            f'<div class="sl"><span class="sn">{num}</span><h2>{title}</h2></div>'
            f'{body}</section>'
        )

    verdict_html = (
        f'<div class="verdict">'
        f'<div class="vt">The honest answer</div>'
        f'<p>{content.get("verdict","")}</p>'
        f'</div>'
    )

    now = datetime.now().strftime("%B %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Moving from {ON} to {DN} (2026) — Complete Guide</title>
<meta name="description" content="{content.get('meta_description','')}">
<link rel="canonical" href="https://moveguide.io/{DC}/moving-from-{OC}-to-{DC}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--g:#1a3c2e;--gold:#c8922a;--cr:#f5f0e8;--bd:#e0d8cc;--mu:#6b6b6b}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'DM Sans',sans-serif;background:var(--cr);color:#1a1a1a;line-height:1.8;font-size:16px}}
/* hero */
.hero{{background:var(--g);color:#fff;padding:64px 24px 52px}}
.hi{{max-width:740px;margin:0 auto}}
.badge{{display:inline-block;background:var(--gold);color:#fff;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;padding:5px 14px;border-radius:20px;margin-bottom:18px}}
h1{{font-family:'Playfair Display',serif;font-size:clamp(28px,5vw,50px);font-weight:900;line-height:1.12;margin-bottom:14px}}
h1 span{{color:var(--gold)}}
.sub{{font-size:17px;color:rgba(255,255,255,.72);max-width:560px}}
/* hero image */
.himg{{position:relative;max-height:420px;overflow:hidden}}
.himg img{{width:100%;object-fit:cover;max-height:420px;display:block}}
.credit{{position:absolute;bottom:8px;right:12px;font-size:11px;color:rgba(255,255,255,.8);background:rgba(0,0,0,.45);padding:3px 10px;border-radius:4px}}
.credit a{{color:inherit;text-decoration:none}}
/* nav */
.toc{{background:#fff;border-bottom:1px solid var(--bd);padding:0 24px;position:sticky;top:0;z-index:99;overflow-x:auto}}
.toc-i{{max-width:740px;margin:0 auto;display:flex;white-space:nowrap}}
.toc a{{display:inline-block;padding:14px 15px;font-size:12px;font-weight:500;color:var(--mu);text-decoration:none;border-bottom:2px solid transparent;transition:.2s}}
.toc a:hover{{color:var(--g);border-bottom-color:var(--gold)}}
/* main */
main{{max-width:740px;margin:0 auto;padding:52px 24px 80px}}
.back{{display:inline-block;color:var(--gold);font-size:14px;font-weight:500;text-decoration:none;margin-bottom:36px}}
/* sections */
.sec{{margin-bottom:60px}}
.sl{{display:flex;align-items:center;gap:12px;margin-bottom:18px}}
.sn{{background:var(--g);color:var(--gold);font-size:11px;font-weight:700;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
h2{{font-family:'Playfair Display',serif;font-size:26px;font-weight:700;color:var(--g)}}
p{{color:#222;margin-bottom:14px;font-size:16px}}
/* verdict */
.verdict{{background:var(--g);border-radius:12px;padding:28px;margin-bottom:4px}}
.vt{{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:var(--gold);font-weight:600;margin-bottom:10px}}
.verdict p{{color:rgba(255,255,255,.88);margin:0;font-size:16px}}
/* list */
.clist{{padding-left:22px;margin:10px 0}}
.clist li{{font-size:15.5px;color:#222;margin-bottom:10px;line-height:1.78}}
/* cta */
.cta{{background:linear-gradient(135deg,var(--g),#0d2a1e);border-radius:14px;padding:40px 28px;text-align:center;margin-top:52px}}
.cta h3{{font-family:'Playfair Display',serif;font-size:26px;color:#fff;margin-bottom:10px}}
.cta p{{color:rgba(255,255,255,.7);margin-bottom:22px}}
.btn{{display:inline-block;background:var(--gold);color:#fff;font-weight:600;font-size:15px;padding:13px 32px;border-radius:8px;text-decoration:none}}
footer{{text-align:center;padding:28px 24px;font-size:12px;color:var(--mu);border-top:1px solid var(--bd)}}
@media(max-width:520px){{.toc a{{padding:13px 9px;font-size:11px}}h2{{font-size:22px}}}}
</style>
</head>
<body>

<section class="hero">
  <div class="hi">
    <div class="badge">2026 Complete Guide</div>
    <h1>Moving from <span>{OE} {ON}</span> to <span>{DE} {DN}</span></h1>
    <p class="sub">{content.get("hero_intro","")}</p>
  </div>
</section>

{img_block}

<nav class="toc"><div class="toc-i">
  <a href="#worth-it">Worth it?</a>
  <a href="#visa">Visa</a>
  <a href="#before">Before you go</a>
  <a href="#arrival">Arrival</a>
  <a href="#first-month">First month</a>
  <a href="#money">Money</a>
  <a href="#work">Work</a>
  <a href="#life">Life</a>
</div></nav>

<main>
  <a class="back" href="/{DC}/">← All {DN} guides</a>

  {sec(1,"worth-it",f"Is it worth moving from {ON} to {DN}?", verdict_html)}
  {sec(2,"visa",f"Visa and permits for {ON} citizens", to_html(content.get("visa","")))}
  {sec(3,"before",f"Before you leave {ON}", to_html(content.get("before_you_leave","")))}
  {sec(4,"arrival",f"Your first week in {DN}", to_html(content.get("arrival","")))}
  {sec(5,"first-month","First month essentials", to_html(content.get("first_month","")))}
  {sec(6,"money",f"Money and cost of living in {DN}", to_html(content.get("money","")))}
  {sec(7,"work",f"Finding work in {DN}", to_html(content.get("work","")))}
  {sec(8,"life",f"Life in {DN} — what to expect", to_html(content.get("life","")))}

  <div class="cta">
    <h3>Planning your move?</h3>
    <p>Browse all our relocation guides for moving to {DN}.</p>
    <a class="btn" href="/{DC}/">All {DN} guides →</a>
  </div>
</main>

<footer>
  <p>© 2026 MoveGuide — Last updated {now} · Always verify visa requirements with official government sources before moving.</p>
</footer>
</body>
</html>"""

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--dest", type=str, default=None)
    args = parser.parse_args()

    # Build all pairs, skip same-country
    pairs = [
        (o, d) for d in DESTINATIONS for o in ORIGINS
        if o["code"] != d["code"]
    ]

    if args.dest:
        pairs = [(o, d) for o, d in pairs if d["code"] == args.dest]

    if args.test:
        pairs = [(o, d) for o, d in pairs if d["code"] == "ireland"][:5]
        log("🧪 TEST MODE — 5 pages")

    total  = len(pairs)
    done   = skipped = failed = 0

    log(f"🚀 {total} pages to generate")

    for i, (origin, dest) in enumerate(pairs, 1):
        out_dir  = PUBLIC_DIR / dest["code"]
        out_dir.mkdir(parents=True, exist_ok=True)
        fname    = f"moving-from-{origin['code']}-to-{dest['code']}.html"
        out_path = out_dir / fname

        # Resume — skip if file already looks complete
        if out_path.exists() and out_path.stat().st_size > 8000:
            log(f"⏭  [{i}/{total}] Skip {origin['name']} → {dest['name']}")
            skipped += 1
            continue

        log(f"⚙️  [{i}/{total}] {origin['name']} → {dest['name']}")

        image   = get_image(f"{dest['capital']} {dest['name']} city skyline")
        content = generate_content(origin, dest)

        if not content:
            log(f"  ❌ FAILED")
            failed += 1
            time.sleep(2)
            continue

        html = build_html(origin, dest, content, image)
        out_path.write_text(html, encoding="utf-8")
        log(f"  ✅ {fname} ({len(html):,} bytes)")
        done += 1
        time.sleep(1.2)   # gentle rate limiting

    log(f"\n{'='*50}")
    log(f"✅ Done:{done}  ⏭ Skipped:{skipped}  ❌ Failed:{failed}  📄 Total:{total}")

if __name__ == "__main__":
    main()

import asyncio
import logging
from core.config import setup_logging, DATA_DIR
from core.database import init_db, lead_exists, insert_lead, update_lead_status, export_leads, fetch_all_leads
from services.scraper import scrape_platform_leads
from services.messenger_agent import score_job_alignment, deploy_outreach_loop

VALID_TARGETS = ["naukri", "glassdoor", "indeed", "foundit"]


def parse_sites(raw):
    raw = (raw or "").lower().replace('"', "").replace("'", "").replace(" ", "")
    if raw in ("all", "default", "any", ""):
        return list(VALID_TARGETS)
    chosen = [p for p in raw.split(",") if p in VALID_TARGETS]
    return chosen or list(VALID_TARGETS)


async def main():
    import argparse

    setup_logging()
    parser = argparse.ArgumentParser(description="Ghost Agent - AI job discovery & outreach (CLI mode)")
    parser.add_argument("--keyword", type=str, default=None)
    parser.add_argument("--location", type=str, default=None)
    parser.add_argument("--min_salary", type=str, default=None)
    parser.add_argument("--sites", type=str, default=None)
    parser.add_argument("--count", type=str, default=None)
    parser.add_argument("--interactive", action="store_true", help="force guided prompts for every option")
    parser.add_argument("--export", action="store_true", help="export stored leads to data/leads.csv and exit")
    args = parser.parse_args()

    if args.export:
        init_db()
        out = export_leads()
        n = len(fetch_all_leads())
        logging.info(f"[+] Exported {n} leads to {out}")
        return

    print("\n" + "=" * 55)
    print("      GHOST PROTOCOL: AUTOMATED OUTREACH")
    print("=" * 55 + "\n")

    init_db()
    resume_path = DATA_DIR / "master_resume.txt"
    try:
        with open(resume_path, "r", encoding="utf-8", errors="replace") as f:
            master_resume = f.read()
    except FileNotFoundError:
        logging.error(f"[-] Could not find {resume_path}. Create it (see sample_resume.txt).")
        return

    force_prompt = args.interactive

    def arg_or_prompt(val, prompt, default):
        if not force_prompt and val:
            return val
        return input(prompt).strip() or default

    keyword = arg_or_prompt(args.keyword, "? Job Role/Keyword (Enter for 'Developer'): ", "Developer")
    location = arg_or_prompt(args.location, "? Target Location (Enter for 'Hyderabad'): ", "Hyderabad")

    raw_sal = arg_or_prompt(args.min_salary, "? Minimum Salary in LPA? (Default: 6.0): ", "6.0")
    try:
        min_lpa = float(raw_sal)
    except ValueError:
        min_lpa = 6.0

    raw_sites = args.sites if (not force_prompt and args.sites) else input("? Sites to search? (naukri, indeed, glassdoor, foundit, all): ").strip()
    platforms = parse_sites(raw_sites)

    raw_count = arg_or_prompt(args.count, "? Jobs to scan per site? (Default: 10): ", "10")
    try:
        target_count = int(raw_count)
    except ValueError:
        target_count = 10

    print("\n[*] Configuration locked. Initializing hunters...")
    print(f"    Targets: {', '.join([p.upper() for p in platforms])}")
    print(f"    Min Pay: {min_lpa} LPA")
    print(f"    Limit: {target_count} jobs per site\n")

    for platform in platforms:
        logging.info(f"[*] Initiating Scraper Engine for {platform.upper()}...")
        leads = await scrape_platform_leads(platform, keyword, location, target_count=target_count, min_lpa=min_lpa)
        if not leads:
            continue

        for lead in leads:
            if lead_exists(lead["id"], lead.get("phone"), lead.get("email")):
                continue
            logging.info(f"[*] AI evaluating fit for: {lead['title']}")
            score, reasoning = await score_job_alignment(lead["jd_text"], master_resume)
            if score >= 5:
                insert_lead(lead["id"], lead["company"], lead["title"], lead.get("phone"), lead.get("email"), lead.get("url"))
                result = await deploy_outreach_loop(lead["id"], lead.get("phone"), lead["title"], lead.get("email"))
                update_lead_status(lead["id"], result.status)
                await asyncio.sleep(90)

    out = export_leads()
    logging.info(f"[+] Leads exported to {out} (also stored in core/ghost_protocol.db)")
    logging.info("[+] Campaign cycle complete.")


if __name__ == "__main__":
    asyncio.run(main())

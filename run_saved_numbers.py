import asyncio
from core.config import setup_logging
from core.database import init_db, fetch_all_leads, update_lead_status, export_leads
from services.messenger_agent import deploy_outreach_loop


async def blast_saved_leads():
    setup_logging()
    import logging

    print("\n" + "=" * 55)
    print("      GHOST PROTOCOL: OUTREACH RE-ENGAGEMENT")
    print("=" * 55 + "\n")

    init_db()
    saved_leads = fetch_all_leads()
    if not saved_leads:
        logging.warning("[-] The database is empty. Run main.py to collect leads first.")
        return

    logging.info(f"[+] Found {len(saved_leads)} leads in the database.")
    proceed = input(f"? Re-run outreach for all {len(saved_leads)} leads? (y/n): ").strip().lower()
    if proceed != "y":
        logging.info("[-] Operation cancelled by user.")
        return

    print("=" * 55 + "\n")
    for row in saved_leads:
        lead_id, company, title, phone, email, url, status = tuple(row)
        logging.info(f"[*] Firing outreach for: {company} - {title} (phone={phone or 'none'}, email={email or 'none'})")
        try:
            result = await deploy_outreach_loop(lead_id, phone, title, email=email)
            update_lead_status(lead_id, result.status)
            logging.info("[*] Waiting 90 seconds before the next contact...")
            await asyncio.sleep(90)
        except Exception as e:
            logging.error(f"[-] Outreach failed for {lead_id}: {e}")
            continue

    export_leads()
    logging.info("[+] Re-engagement campaign finished. Leads re-exported to data/leads.csv.")


if __name__ == "__main__":
    asyncio.run(blast_saved_leads())

import asyncio
import logging
import re
import random
import urllib.parse
from playwright.async_api import async_playwright
from core.config import SESSION_DIR, browser_launch_kwargs
from dotenv import load_dotenv

load_dotenv()

def extract_indian_phone(text: str) -> str:
    phone_regex = r'(?:\+91[\-\s]?)?[6-9]\d{9}\b'
    match = re.search(phone_regex, text)
    if match:
        clean_num = re.sub(r'\D', '', match.group())
        return "91" + clean_num if len(clean_num) == 10 else clean_num
    return ""

def is_salary_adequate(text: str, min_lpa: float = 6.0) -> bool:
    text_lower = text.lower().replace('\n', ' ').replace(',', '')
    min_annual = min_lpa * 100000
    
    lpa_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:lacs?|lakhs?|lpa)', text_lower)
    if lpa_matches:
        max_val = max([float(m) for m in lpa_matches])
        if max_val < min_lpa: return False 
        return True      

    currency_range = re.findall(r'(?:\u20B9|rs\.?|inr)\s*(\d{4,7})\s*(?:-|to)\s*(?:\u20B9|rs\.?|inr)?\s*(\d{4,7})|(\d{4,7})\s*(?:-|to)\s*(?:\u20B9|rs\.?|inr)\s*(\d{4,7})', text_lower)
    k_range = re.findall(r'(\d+(?:\.\d+)?)\s*k\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*k', text_lower)
    
    tier_2_maxes = []
    for match in currency_range:
        nums = [float(n) for n in match if n]
        if nums: tier_2_maxes.append(max(nums))
            
    for m1, m2 in k_range:
        tier_2_maxes.append(max(float(m1), float(m2)) * 1000)

    if tier_2_maxes:
        max_val = max(tier_2_maxes)
        annualized = max_val * 12 if max_val < 100000 else max_val
        if annualized < min_annual: return False
        return True

    naked_ranges = re.findall(r'(\d{4,7})\s*(?:-|to)\s*(\d{4,7})', text_lower)
    if naked_ranges:
        max_val = max([float(high) for _, high in naked_ranges])
        annualized = max_val * 12 if max_val < 100000 else max_val
        if annualized < min_annual: return False
        return True
        
    anchored_single = re.findall(r'(?:salary|pay|ctc|compensation)[\s\w]*?(?:\u20B9|rs\.?|inr)\s*(\d{4,7})', text_lower)
    if anchored_single:
        max_val = max([float(m) for m in anchored_single])
        annualized = max_val * 12 if max_val < 100000 else max_val
        if annualized < min_annual: return False
        return True

    return True

async def human_delay(min_sec: float = 1.5, max_sec: float = 4.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def close_rogue_tabs(context, main_page):
    try:
        for p in context.pages:
            if p != main_page:
                await p.close()
        await main_page.bring_to_front()
    except Exception:
        pass

async def dismiss_overlays(page):
    try:
        popup_selectors = [
            "span.ni-gnb-icn-close", 
            "div.crossIcon", 
            "button.close", 
            "[aria-label='close']", 
            ".modal-close",
            "div.styles_close-icon__b4z_Y"
        ]
        for selector in popup_selectors:
            locator = page.locator(selector).first
            if await locator.is_visible():
                logging.info(f"    [!] Ghost Agent detected popup overlay ({selector}). Dismissing...")
                await locator.click(timeout=2000)
                await asyncio.sleep(1)
    except Exception: pass

def get_paginated_url(platform: str, keyword: str, location: str, page_num: int) -> str:
    formatted_kw = urllib.parse.quote(keyword.strip())
    formatted_loc = urllib.parse.quote(location.strip())
    
    if platform == "naukri":
        base_kw = keyword.strip().lower().replace(' ', '-')
        base_loc = location.strip().lower().replace(' ', '-')
        if page_num == 1: return f"https://www.naukri.com/{base_kw}-jobs-in-{base_loc}?k={formatted_kw}&l={formatted_loc}&sort=r&f=30"
        return f"https://www.naukri.com/{base_kw}-jobs-in-{base_loc}-{page_num}?k={formatted_kw}&l={formatted_loc}&sort=r&f=30"
    elif platform == "indeed":
        start_count = (page_num - 1) * 10
        return f"https://in.indeed.com/jobs?q={formatted_kw}&l={formatted_loc}&sort=date&fromage=30&start={start_count}"
    elif platform == "glassdoor":
        return f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={formatted_kw}&locName={formatted_loc}&sortBy=date_desc&fromAge=30&p={page_num}"
    elif platform == "foundit":
        start_count = (page_num - 1) * 15
        return f"https://www.foundit.in/srp/results?query={formatted_kw}&locations={formatted_loc}&sort=1&timeFrame=30&start={start_count}"
    return ""

async def scrape_platform_leads(platform: str, keyword: str, location: str, target_count: int = 10, min_lpa: float = 6.0):
    async with async_playwright() as p:
        logging.info(f"[*] Launching context for {platform.upper()}...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR / f"{platform}_profile",
            viewport={"width": random.randint(1280, 1920), "height": random.randint(800, 1080)},
            **browser_launch_kwargs()
        )
        page = await context.new_page()
        captured_leads = []
        clicked_urls = set()
        page_num = 1
        
        is_split_pane = platform in ["indeed", "glassdoor"]
        if platform == "naukri": card_selector = "a[href*='job-listings-']"
        elif platform == "indeed": card_selector = "a.jcs-JobTitle"
        elif platform == "glassdoor": card_selector = "a[data-test='job-link'], a[data-test='job-title']"
        elif platform == "foundit": card_selector = "div.job-tittle a"

        while len(captured_leads) < target_count:
            url = get_paginated_url(platform, keyword, location, page_num)
            try:
                logging.info(f"[*] Loading Page {page_num}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await human_delay(3.0, 5.0)
                await dismiss_overlays(page)
                
                if page_num == 1:
                    try:
                        if platform == "naukri":
                            relevance_btn = page.get_by_text("Relevance", exact=True).first
                            if await relevance_btn.is_visible():
                                await relevance_btn.click(timeout=3000)
                                await human_delay(1.0, 2.0)
                                date_btn = page.get_by_text("Date", exact=True).first
                                await date_btn.click(timeout=3000)
                                await page.wait_for_selector(card_selector, timeout=15000)
                                await human_delay(3.0, 5.0)
                        elif platform == "indeed":
                            sort_date = page.locator("a").filter(has_text=re.compile(r"sort by date", re.IGNORECASE)).first
                            if await sort_date.is_visible():
                                await sort_date.click(timeout=3000)
                                await page.wait_for_selector(card_selector, timeout=15000)
                                await human_delay(3.0, 5.0)
                    except Exception: pass
            except Exception as e:
                logging.error(f"[-] Load timed out on page {page_num}: {e}")
                break

            await dismiss_overlays(page)
            job_cards = page.locator(card_selector)
            total_found = await job_cards.count()
            
            logging.info(f"[*] Discovered {total_found} listings on Page {page_num}.")
            if total_found == 0: break

            new_unique_jobs = 0

            for i in range(total_found):
                if len(captured_leads) >= target_count: break
                
                try:
                    card = job_cards.nth(i)
                    job_url = await card.get_attribute("href")
                except Exception: continue

                # FAIL-FAST 1: Instant Skip for Duplicates
                if not job_url or job_url in clicked_urls: 
                    continue
                
                clicked_urls.add(job_url)
                new_unique_jobs += 1
                
                try:
                    await card.scroll_into_view_if_needed()
                    await human_delay(0.5, 1.0)
                    await dismiss_overlays(page)
                    card_text = await card.inner_text()
                except Exception: continue
                
                job_title = card_text.split('\n')[0].strip() if card_text else "Unknown"

                # FAIL-FAST 2: Instant Skip for Low Salary
                if not is_salary_adequate(card_text, min_lpa=min_lpa):
                    logging.info(f"    [-] Skipping: Card shows salary under {min_lpa} LPA. ({job_title})")
                    continue

                logging.info(f"[*] [{len(captured_leads)+1}/{target_count}] Processing: {job_title}")
                
                job_page = None
                try:
                    if is_split_pane:
                        await card.click(timeout=10000)
                        job_page = page 
                        await human_delay(3.0, 5.0) 
                        if platform == "indeed": content_locator = job_page.locator(".jobsearch-RightPane, .jobsearch-JobComponent").first
                        else: content_locator = job_page.locator(".job-details, [data-test='jobDetails']").first
                        try:
                            expand_buttons = content_locator.locator("button, a, span").filter(has_text=re.compile(r"(read|show|view)\s+more|about\s+company", re.IGNORECASE))
                            if await expand_buttons.count() > 0:
                                await expand_buttons.first.click(timeout=3000)
                                await human_delay(1.5, 2.5)
                                await close_rogue_tabs(context, job_page)
                        except: pass
                        await content_locator.hover(timeout=5000)
                        for _ in range(random.randint(2, 4)): await job_page.mouse.wheel(0, random.randint(400, 800))
                        try: jd_text = await content_locator.inner_text()
                        except: jd_text = ""
                        page_text = jd_text
                    else:
                        async with context.expect_page() as new_page_info: await card.click(timeout=10000, force=True)
                        job_page = await new_page_info.value
                        await job_page.bring_to_front()
                        await job_page.wait_for_load_state("domcontentloaded")
                        await human_delay(2.0, 4.0)
                        try:
                            jd_section = job_page.locator(".job-desc, [data-test='job-description'], .jd-container, .job-description").first
                            expand_buttons = jd_section.locator("button, a, span").filter(has_text=re.compile(r"(read|show|view)\s+more", re.IGNORECASE))
                            if await expand_buttons.count() > 0:
                                await expand_buttons.first.click(timeout=3000)
                                await human_delay(0.8, 1.5)
                        except Exception: pass
                        for _ in range(random.randint(2, 4)):
                            await job_page.evaluate(f"window.scrollBy(0, {random.randint(400, 800)});")
                            await human_delay(0.8, 2.0)
                        page_text = await job_page.content()
                        try: jd_text = await job_page.locator("body").inner_text()
                        except: jd_text = page_text

                    if not is_salary_adequate(jd_text, min_lpa=min_lpa):
                        logging.info(f"    [-] Skipping: Found hidden salary inside description under {min_lpa} LPA. ({job_title})")
                        continue

                    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    emails_found = list(set(re.findall(email_regex, page_text)))
                    target_email = emails_found[0] if emails_found else None
                    phone_discovered = extract_indian_phone(page_text)
                    
                    if phone_discovered or target_email:
                        full_url = job_url
                        if full_url and full_url.startswith('/'):
                            domains = {"naukri": "https://www.naukri.com", "indeed": "https://in.indeed.com", "glassdoor": "https://www.glassdoor.co.in", "foundit": "https://www.foundit.in"}
                            full_url = domains.get(platform, "") + full_url

                        captured_leads.append({
                            "id": f"{platform}_{len(captured_leads)}_{phone_discovered or target_email}",
                            "title": job_title, "company": "Target Company", "phone": phone_discovered,
                            "email": target_email, "url": full_url, "jd_text": jd_text[:2500]
                        })
                        logging.info(f"    [+] Captured Data -> Phone: {phone_discovered} | Email: {target_email}")
                    else:
                        logging.warning("    [-] No contact data found after expansion.")

                except Exception as loop_err:
                    logging.error(f"    [-] Navigation/Click roadblock: {loop_err}")
                finally:
                    if is_split_pane and job_page: await close_rogue_tabs(context, page)
                    if not is_split_pane and job_page:
                        try: await job_page.close()
                        except: pass
                    await human_delay(2.0, 4.0)
            
            # THE SAFETY BREAKER
            if new_unique_jobs == 0:
                logging.warning("    [!] Exhausted all unique jobs. Website is recycling old listings. Stopping pagination.")
                break

            page_num += 1

        await context.close()
        return captured_leads
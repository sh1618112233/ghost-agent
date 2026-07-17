import asyncio
import logging
import json
import httpx
import re
import urllib.parse
import aiosmtplib
from email.message import EmailMessage
from playwright.async_api import async_playwright
from core.config import SESSION_DIR, browser_launch_kwargs, MODEL_NAME, OLLAMA_URL, SMTP_EMAIL, SMTP_PASSWORD, SMTP_HOST, SMTP_PORT
from dotenv import load_dotenv

load_dotenv()

async def score_job_alignment(jd_text: str, resume_text: str) -> int:
    """Uses local AI to evaluate fit, truncates text for speed, and forces hard prints."""
    
    # 1. Truncate job description to speed up the local AI
    short_jd = jd_text[:1000] 
    
    prompt = f"""
    You are an expert technical recruiter. Read this Job Description and this candidate's Resume.
    Evaluate the match and respond ONLY in valid JSON format.
    
    Use this exact JSON structure:
    {{
        "reasoning": "Write 1 specific sentence explaining exactly why they are or are not a good fit based on the required skills.",
        "score": <insert integer from 1 to 10 here>
    }}
    
    Job Description: {short_jd}
    
    Resume: {resume_text}
    """
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "format": "json"}
        async with httpx.AsyncClient() as client:
            res = await client.post(OLLAMA_URL, json=payload, timeout=120.0)
            
            raw_response = res.json().get("response", "").strip()
            
            # 2. Unbreakable Markdown stripping (No multi-line regex)
            clean_json_string = raw_response
            if clean_json_string.startswith("```"):
                clean_json_string = clean_json_string.strip("`").strip()
                if clean_json_string.startswith("json"):
                    clean_json_string = clean_json_string[4:].strip()
            
            try:
                # 3. Parse JSON
                ai_data = json.loads(clean_json_string)
                reasoning = ai_data.get("reasoning", "No reasoning provided.")
                score = int(ai_data.get("score", 5))
                
            except json.JSONDecodeError:
                # 4. Fallback Regex if JSON is malformed
                reason_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', clean_json_string, re.IGNORECASE)
                reasoning = reason_match.group(1) if reason_match else "AI provided malformed text."
                
                score_match = re.search(r'"score"\s*:\s*(\d+)', clean_json_string, re.IGNORECASE)
                score = int(score_match.group(1)) if score_match else 5

# 5. Hard Print to Terminal
            print("\n" + "-"*50)
            print(f"?? AI REASONING: {reasoning}")
            print("-" * 50 + "\n")
            
            # RETURN BOTH THE SCORE AND THE REASONING
            return score, reasoning
            
    except Exception as e:
        print(f"\n[? AI PIPELINE ERROR]: {e}\n")
        # Return a safe score and the error reason
        return 5, f"Pipeline Error: {e}"

async def send_email_fallback(target_email: str, job_title: str):
    """Executes the Waterfall protocol if WhatsApp is unavailable."""
    sender_email = SMTP_EMAIL
    sender_pass = SMTP_PASSWORD
    
    if not sender_email or not sender_pass:
        logging.warning("    [-] Email fallback skipped. Credentials missing in .env.")
        return False
        
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Application for {job_title}"
        msg['From'] = sender_email
        msg['To'] = target_email
        msg.set_content(f"Hi there,\n\nI recently came across your opening for the {job_title} role. Given my background in application support, I believe I would be a strong fit. Please let me know if I can share my resume with you for review.\n\nBest regards.")
        
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=sender_email,
            password=sender_pass
        )
        logging.info(f"    [?? SUCCESS] Emailed outreach directly to {target_email}.")
        return True
    except Exception as e:
        logging.error(f"    [-] Email fallback failed: {e}")
        return False

async def deploy_outreach_loop(lead_id: str, phone: str, title: str, email: str = None):
    """Physically opens WhatsApp Web and sends the initial outreach message."""
    if not phone:
        logging.info("    [*] No phone number found. Triggering Email Waterfall Protocol.")
        if email: 
            await send_email_fallback(email, title)
        return

    logging.info(f"[*] Attempting WhatsApp Outreach for {phone}...")
    
    message = f"Hi! I saw you are recruiting for the {title} position.Is the position available?"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR / "whatsapp_profile",
            **browser_launch_kwargs()
        )
        
        page = await context.new_page()
        
        try:
            logging.info("    ? Loading WhatsApp Web interface...")
            await page.goto(whatsapp_url, timeout=60000)
            
            try:
                send_button = page.locator("button[aria-label='Send'], span[data-icon='send']")
                await send_button.wait_for(state="visible", timeout=45000)
                
                await asyncio.sleep(2)
                await send_button.click()
                logging.info(f"    [? SUCCESS] WhatsApp message successfully delivered to {phone}!")
                await asyncio.sleep(3) 
                
            except Exception:
                invalid_dialog = page.locator("text='Phone number shared via url is invalid'")
                if await invalid_dialog.count() > 0:
                    logging.warning(f"    [-] Number {phone} is not registered on WhatsApp.")
                    if email:
                        logging.info("    [*] Triggering Email Waterfall Protocol...")
                        await send_email_fallback(email, title)
                else:
                    logging.error("    [-] Timed out waiting for WhatsApp to load. (Did you scan the QR code?)")
                    
        except Exception as e:
            logging.error(f"    [-] WhatsApp navigation error: {e}")
            
        finally:
            await page.close()
            await context.close()
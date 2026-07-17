import asyncio
import httpx
import json

MODEL_NAME = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

async def test_the_ai():
    print("\n[!] WAKING UP THE AI...")
    
    prompt = """
    You are an expert technical recruiter. Read this Job Description and this candidate's Resume.
    Evaluate the match and respond ONLY in valid JSON format.
    
    Use this exact JSON structure:
    {
        "reasoning": "Write 1 sentence here.",
        "score": 8
    }
    
    Job Description: We need a Python developer with 5 years of AWS experience.
    Resume: I am an L2 Application Support engineer with ServiceNow experience.
    """
    
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "format": "json"}
    
    try:
        print("[!] SENDING REQUEST TO OLLAMA...")
        async with httpx.AsyncClient() as client:
            # Increased timeout to 60 seconds just in case your machine is processing slowly
            res = await client.post(OLLAMA_URL, json=payload, timeout=60.0)
            
            print("\n" + "="*40)
            print("RAW UNFILTERED OUTPUT FROM AI:")
            print("="*40)
            
            raw_text = res.json().get("response", "")
            print(raw_text)
            
            print("="*40)
            
    except Exception as e:
        print(f"\n[FATAL ERROR]: The connection failed completely: {e}")

if __name__ == "__main__":
    asyncio.run(test_the_ai())
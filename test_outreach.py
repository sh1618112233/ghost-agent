"""WhatsApp OutreachResult verification.

Run:  python test_outreach.py

Matches the repo's existing test style (bare asyncio.run script, no pytest).
Fakes Playwright so no browser, QR scan, network, or SMTP is required.
"""
import asyncio
import logging
import types

import services.messenger_agent as messenger
from services.messenger_agent import OutreachResult, deploy_outreach_loop

logging.disable(logging.CRITICAL)  # keep test output clean


# --- fake Playwright surface -------------------------------------------------

class FakeLocator:
    def __init__(self, scenario):
        self.scenario = scenario

    async def wait_for(self, state=None, timeout=None):
        if self.scenario in ("qr_timeout", "button_missing", "invalid_number"):
            raise Exception("timeout waiting for selector")

    async def click(self):
        pass

    async def count(self):
        return 1 if self.scenario == "invalid_number" else 0


class FakePage:
    def __init__(self, scenario):
        self.scenario = scenario

    async def goto(self, url, timeout=None):
        if self.scenario == "nav_fail":
            raise Exception("net::ERR_FAILED")

    def locator(self, selector):
        return FakeLocator(self.scenario)

    async def close(self):
        pass


class FakeContext:
    def __init__(self, scenario):
        self.scenario = scenario

    async def new_page(self):
        if self.scenario == "unexpected_error":
            raise Exception("unexpected failure creating page")
        return FakePage(self.scenario)

    async def close(self):
        pass


class FakeChromium:
    def __init__(self, scenario):
        self.scenario = scenario

    async def launch_persistent_context(self, user_data_dir=None, **kwargs):
        if self.scenario == "browser_crash":
            raise Exception("failed to launch browser")
        return FakeContext(self.scenario)


class FakePlaywright:
    def __init__(self, scenario):
        self.chromium = FakeChromium(scenario)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


# --- test harness ------------------------------------------------------------

def install_fake(scenario, email_calls):
    messenger.async_playwright = lambda: FakePlaywright(scenario)

    async def fake_email(target_email, job_title):
        email_calls.append((target_email, job_title))
        return True

    messenger.send_email_fallback = fake_email
    # make asyncio.sleep instant so the suite is fast and deterministic
    messenger.asyncio = types.SimpleNamespace(sleep=lambda *a, **k: asyncio.sleep(0))


async def run_case(name, scenario, phone, email, expect_success, expect_status, expect_email=False):
    email_calls = []
    install_fake(scenario, email_calls)
    result = await deploy_outreach_loop("lead_1", phone, "L2 Support", email=email)

    ok = (result.success == expect_success) and (result.status == expect_status)
    email_ok = (len(email_calls) > 0) if expect_email else (len(email_calls) == 0)
    status = "PASS" if (ok and email_ok) else "FAIL"
    print(f"[{status}] {name}: success={result.success} status={result.status} "
          f"reason={result.reason!r} email_calls={len(email_calls)}")
    assert ok, f"{name}: expected success={expect_success} status={expect_status}, got {result}"
    assert email_ok, f"{name}: email expectation {expect_email} not met ({len(email_calls)} calls)"
    return result


async def main():
    print("\n=== WhatsApp OutreachResult tests ===\n")

    await run_case("Test 1 valid WhatsApp number     -> CONTACTED",
                  "valid", "919876543210", None, True, "CONTACTED")
    await run_case("Test 2 no phone number           -> NO_PHONE",
                  "valid", "", "recruiter@example.com", False, "NO_PHONE", expect_email=True)
    await run_case("Test 3 invalid WhatsApp number  -> INVALID_NUMBER",
                  "invalid_number", "919876543210", "recruiter@example.com",
                  False, "INVALID_NUMBER", expect_email=True)
    await run_case("Test 4 QR not scanned           -> SEND_FAILED",
                  "qr_timeout", "919876543210", None, False, "SEND_FAILED")
    await run_case("Test 5 send button missing       -> SEND_FAILED",
                  "button_missing", "919876543210", None, False, "SEND_FAILED")
    await run_case("Test 6 Playwright nav failure    -> SEND_FAILED",
                  "nav_fail", "919876543210", None, False, "SEND_FAILED")
    await run_case("Test 7 unexpected exception      -> SEND_FAILED",
                  "unexpected_error", "919876543210", None, False, "SEND_FAILED")

    # extra: browser launch crash also collapses to SEND_FAILED
    await run_case("Test 8 browser launch crash     -> SEND_FAILED",
                  "browser_crash", "919876543210", None, False, "SEND_FAILED")

    print("\nAll outreach tests passed.")


if __name__ == "__main__":
    asyncio.run(main())

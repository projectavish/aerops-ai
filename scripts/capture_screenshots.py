"""Capture dashboard screenshots for README using Playwright."""
import asyncio
import time
from pathlib import Path

from playwright.async_api import async_playwright


TABS = [
    ("overview", None, "AerOps AI - Executive Overview & KPI Dashboard"),
    ("delay_analysis", "Delay Analysis", "Delay Analysis - IATA Root Cause Breakdown"),
    ("delay_prediction", "Delay Prediction", "ML Delay Prediction Engine"),
    ("eu261", "EU261 Exposure", "EU261 Financial Exposure Calculator"),
    ("turnaround", "Turnaround", "Turnaround Performance Analysis"),
    ("disruption", "Disruption Recovery", "Disruption Recovery Simulator"),
]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
BASE_URL = "http://localhost:8504"


async def capture_screenshots():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"Navigating to {BASE_URL}...")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(4)  # Wait for Streamlit to fully render

        # Screenshot 1: Overview (scroll to top)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        path = OUTPUT_DIR / "01_overview.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"Saved: {path.name}")

        # Find and click each tab
        for slug, tab_name, description in TABS[1:]:
            print(f"Clicking tab: {tab_name}")
            try:
                tab = page.get_by_role("tab", name=tab_name)
                await tab.click()
                await asyncio.sleep(3)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)

                num = TABS.index((slug, tab_name, description)) + 1
                path = OUTPUT_DIR / f"0{num}_{slug}.png"
                await page.screenshot(path=str(path), full_page=False)
                print(f"Saved: {path.name}")
            except Exception as e:
                print(f"  Warning: {e}")

        await browser.close()
        print(f"\nAll screenshots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())

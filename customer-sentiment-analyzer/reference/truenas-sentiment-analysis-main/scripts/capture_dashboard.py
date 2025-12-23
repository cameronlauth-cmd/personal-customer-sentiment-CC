"""
Capture screenshots of all dashboard pages.
Saves to outputs/screenshots/ for review.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Dashboard URL
BASE_URL = "http://localhost:8501"

# Pages to capture (click sidebar links)
PAGES = [
    (None, "home"),  # Main page - no click needed
    ("Overview", "1_overview"),
    ("Cases", "2_cases"),
    ("Timeline", "3_timeline"),
    ("Trends", "4_trends"),
    ("Export", "5_export"),
]

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "screenshots"


async def capture_screenshots():
    """Capture screenshots of all dashboard pages."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        print(f"Capturing dashboard screenshots to {OUTPUT_DIR}")
        print()

        # First load the home page
        print(f"  Loading home page: {BASE_URL}")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)  # Wait for Streamlit to fully load

        for page_name, filename in PAGES:
            try:
                if page_name:
                    # Click the sidebar link
                    print(f"  Clicking: {page_name}")

                    # Try to find and click the sidebar link
                    # Streamlit sidebar links are in the nav
                    link = page.get_by_role("link", name=page_name)
                    await link.click()
                    await page.wait_for_timeout(3000)  # Wait for page to render
                else:
                    print(f"  Capturing: Home")

                # Take screenshot
                screenshot_path = OUTPUT_DIR / f"{filename}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"    Saved: {screenshot_path.name}")

            except Exception as e:
                print(f"    Error on {page_name or 'home'}: {e}")

        await browser.close()

    print()
    print(f"Done! Screenshots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())

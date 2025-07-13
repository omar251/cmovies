#!/usr/bin/env python3
"""Simple test script to debug the iframe issue without full dependencies."""

import asyncio
import sys

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not available. Run: pip install playwright && playwright install chromium")
    PLAYWRIGHT_AVAILABLE = False

async def simple_debug_test():
    """Simple test to see what's on the vidsrc.xyz page."""
    
    if not PLAYWRIGHT_AVAILABLE:
        return
    
    url = "https://vidsrc.xyz/embed/movie/0133093"  # The Matrix
    
    print(f"Testing URL: {url}")
    print("Opening browser in visible mode...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Visible browser
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        try:
            page = await browser.new_page()
            
            # Set user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print("Navigating to page...")
            await page.goto(url, wait_until="networkidle", timeout=45000)
            
            print(f"Page loaded. Title: {await page.title()}")
            print(f"Current URL: {page.url}")
            
            # Wait for page to fully load
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)  # Wait 3 seconds
            
            # Check for iframes
            iframe_count = await page.evaluate("document.querySelectorAll('iframe').length")
            print(f"Found {iframe_count} iframe(s)")
            
            if iframe_count > 0:
                # Get iframe details
                iframe_info = await page.evaluate("""
                    Array.from(document.querySelectorAll('iframe')).map((iframe, index) => ({
                        index: index,
                        src: iframe.src,
                        id: iframe.id,
                        className: iframe.className,
                        width: iframe.width,
                        height: iframe.height
                    }))
                """)
                
                print("Iframe details:")
                for info in iframe_info:
                    print(f"  Iframe {info['index']}: src='{info['src']}', id='{info['id']}', class='{info['className']}'")
            else:
                print("No iframes found. Checking page content...")
                
                # Get page content info
                body_text = await page.evaluate("document.body ? document.body.innerText.substring(0, 500) : 'No body'")
                print(f"Page content preview: {body_text}")
                
                # Check for any error messages or redirects
                page_html = await page.content()
                if "error" in page_html.lower() or "not found" in page_html.lower():
                    print("⚠️  Page might contain error messages")
                
                if "redirect" in page_html.lower():
                    print("⚠️  Page might be redirecting")
            
            print("\nWaiting 10 seconds for you to inspect the browser...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            await browser.close()

def main():
    if not PLAYWRIGHT_AVAILABLE:
        print("Please install playwright:")
        print("1. pip install playwright")
        print("2. playwright install chromium")
        return
    
    print("Simple vidsrc.xyz Debug Test")
    print("=" * 30)
    asyncio.run(simple_debug_test())

if __name__ == "__main__":
    main()
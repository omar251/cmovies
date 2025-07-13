import asyncio
from playwright.async_api import async_playwright, Page, Request, TimeoutError as PlaywrightTimeoutError

async def get_m3u8_url(page_url: str):
    """
    Launches a headless browser, navigates to the given URL,
    and attempts to find an M3U8 URL by monitoring network requests.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print(f"Navigating to {page_url}...")
        try:
            await page.goto(page_url, wait_until="networkidle", timeout=30000)

            print("Locating initial iframe...")
            initial_iframe_element = await page.wait_for_selector("iframe", timeout=10000)
            initial_frame = await initial_iframe_element.content_frame()
            if not initial_frame:
                print("Could not find the initial iframe.")
                return None

            print("Setting up M3U8 listener...")
            async with page.expect_request("**/*.m3u8", timeout=30000) as request_info:
                try:
                    print("Waiting for play button...")
                    await initial_frame.wait_for_selector("#pl_but_background", timeout=5000)
                    print("Clicking the initial play button...")
                    await initial_frame.evaluate('document.querySelector("#pl_but_background").click()')
                except PlaywrightTimeoutError:
                    print("Timeout: Could not find or click the initial play button.")
                    return None

                try:
                    print("Waiting for the player iframe to load...")
                    player_iframe_element = await page.wait_for_selector(
                        'iframe[id="player_iframe"]', timeout=10000
                    )
                    player_frame = await player_iframe_element.content_frame()
                    if not player_frame:
                        print("Could not get frame from player iframe element.")
                        return None
                except PlaywrightTimeoutError:
                    print("Timeout: Player iframe did not appear after click.")
                    return None

                print("Attempting to start video in player iframe...")
                try:
                    await player_frame.click("body", timeout=5000)
                except PlaywrightTimeoutError:
                    print("Could not click in player iframe, assuming autoplay.")

                print("Waiting for M3U8 URL...")
                request = await request_info.value

            m3u8_url = request.url
            print(f"\nFound M3U8 URL: {m3u8_url}\n")
            return m3u8_url

        except PlaywrightTimeoutError:
            print("Timeout: Did not receive an M3U8 request in time.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        finally:
            await browser.close()

# --- Main execution ---
# Target URL
video_page_url = "https://vidsrc.xyz/embed/movie/"
video_page_url += input("Enter imdb ID: ")

if __name__ == "__main__":
    print("Starting headless browser to find M3U8...")
    extracted_m3u8 = asyncio.run(get_m3u8_url(video_page_url))
    if extracted_m3u8:
        print(f"Successfully extracted M3U8: {extracted_m3u8}")
    else:
        print("Failed to extract M3U8 URL.")

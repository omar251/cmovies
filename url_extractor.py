"""M3U8 URL extraction functionality using Playwright."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from config import (
    NAVIGATION_TIMEOUT, ELEMENT_WAIT_TIMEOUT, CLICK_TIMEOUT, M3U8_REQUEST_TIMEOUT,
    INITIAL_IFRAME_SELECTOR, PLAY_BUTTON_SELECTOR, PLAYER_IFRAME_SELECTOR,
    VIDSRC_BASE_URL
)
from utils import validate_url, validate_imdb_id, clean_imdb_id

logger = logging.getLogger(__name__)

class URLExtractionError(Exception):
    """Custom exception for URL extraction errors."""
    pass

class M3U8Extractor:
    """Handles M3U8 URL extraction from vidsrc.xyz."""

    def __init__(self, headless: bool = True):
        """
        Initialize the M3U8Extractor.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        logger.info(f"M3U8Extractor initialized (headless={headless})")

    def build_url(self, imdb_id: str) -> str:
        """
        Build the vidsrc.xyz URL from IMDb ID.

        Args:
            imdb_id: The IMDb ID

        Returns:
            Complete vidsrc.xyz URL

        Raises:
            URLExtractionError: If IMDb ID is invalid
        """
        if not validate_imdb_id(imdb_id):
            raise URLExtractionError(f"Invalid IMDb ID: {imdb_id}")

        # Get the IMDb ID with 'tt' prefix
        cleaned_id = clean_imdb_id(imdb_id)
        # vidsrc.xyz expects the full IMDb ID WITH the 'tt' prefix
        url = f"{VIDSRC_BASE_URL}{cleaned_id}"

        logger.info(f"Built URL: {url} (from IMDb ID: {cleaned_id})")
        return url

    async def extract_from_url(self, page_url: str) -> Optional[str]:
        """
        Extract M3U8 URL from the given page URL.

        Args:
            page_url: The vidsrc.xyz embed URL

        Returns:
            M3U8 URL if found, None otherwise

        Raises:
            URLExtractionError: If extraction fails
        """
        if not validate_url(page_url):
            raise URLExtractionError(f"Invalid URL: {page_url}")

        logger.info(f"Starting M3U8 extraction from: {page_url}")

        async with async_playwright() as p:
            browser = None
            try:
                # Launch browser with additional options to avoid detection
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                page = await browser.new_page()
                
                # Set a realistic user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                # Remove webdriver property
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)

                # Navigate to the page
                logger.info("Navigating to page...")
                await page.goto(page_url, wait_until="networkidle", timeout=NAVIGATION_TIMEOUT)

                # Find initial iframe
                logger.info("Locating initial iframe...")
                logger.info(f"Page URL: {page.url}")
                logger.info(f"Page title: {await page.title()}")
                
                # Check if page loaded properly
                await page.wait_for_load_state("domcontentloaded")
                
                # Look for any iframes on the page
                iframe_count = await page.evaluate("document.querySelectorAll('iframe').length")
                logger.info(f"Found {iframe_count} iframe(s) on the page")
                
                if iframe_count == 0:
                    # Wait a bit more for dynamic content
                    logger.info("No iframes found immediately, waiting for dynamic content...")
                    await page.wait_for_timeout(5000)
                    iframe_count = await page.evaluate("document.querySelectorAll('iframe').length")
                    logger.info(f"After waiting: Found {iframe_count} iframe(s)")
                
                initial_iframe_element = await page.wait_for_selector(
                    INITIAL_IFRAME_SELECTOR, timeout=ELEMENT_WAIT_TIMEOUT
                )
                initial_frame = await initial_iframe_element.content_frame()

                if not initial_frame:
                    raise URLExtractionError("Could not access initial iframe content")

                # Set up M3U8 listener and perform actions
                logger.info("Setting up M3U8 request listener...")
                async with page.expect_request("**/*.m3u8", timeout=M3U8_REQUEST_TIMEOUT) as request_info:

                    # Click the play button
                    await self._click_play_button(initial_frame)

                    # Wait for and interact with player iframe
                    await self._interact_with_player(page)

                    # Wait for M3U8 request
                    logger.info("Waiting for M3U8 request...")
                    request = await request_info.value

                m3u8_url = request.url
                logger.info(f"Successfully extracted M3U8 URL: {m3u8_url}")
                return m3u8_url

            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout during extraction: {e}")
                raise URLExtractionError(f"Timeout during extraction: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during extraction: {e}")
                raise URLExtractionError(f"Extraction failed: {e}")
            finally:
                if browser:
                    await browser.close()
                    logger.info("Browser closed")

    async def _click_play_button(self, frame) -> None:
        """
        Click the play button in the initial iframe.

        Args:
            frame: The iframe content frame

        Raises:
            URLExtractionError: If play button cannot be found or clicked
        """
        try:
            logger.info("Looking for play button...")
            await frame.wait_for_selector(PLAY_BUTTON_SELECTOR, timeout=ELEMENT_WAIT_TIMEOUT)

            logger.info("Clicking play button...")
            await frame.evaluate(f'document.querySelector("{PLAY_BUTTON_SELECTOR}").click()')

            logger.info("Play button clicked successfully")

        except PlaywrightTimeoutError:
            raise URLExtractionError("Could not find or click the play button")
        except Exception as e:
            raise URLExtractionError(f"Failed to click play button: {e}")

    async def _interact_with_player(self, page) -> None:
        """
        Wait for and interact with the player iframe.

        Args:
            page: The main page object

        Raises:
            URLExtractionError: If player iframe cannot be found or interacted with
        """
        try:
            logger.info("Waiting for player iframe...")
            player_iframe_element = await page.wait_for_selector(
                PLAYER_IFRAME_SELECTOR, timeout=ELEMENT_WAIT_TIMEOUT
            )

            player_frame = await player_iframe_element.content_frame()
            if not player_frame:
                raise URLExtractionError("Could not access player iframe content")

            logger.info("Attempting to start video in player iframe...")
            try:
                await player_frame.click("body", timeout=CLICK_TIMEOUT)
                logger.info("Clicked in player iframe")
            except PlaywrightTimeoutError:
                logger.info("Could not click in player iframe, assuming autoplay")

        except PlaywrightTimeoutError:
            raise URLExtractionError("Player iframe did not appear after clicking play button")
        except Exception as e:
            raise URLExtractionError(f"Failed to interact with player: {e}")

    async def extract_from_imdb_id(self, imdb_id: str) -> Optional[str]:
        """
        Extract M3U8 URL using IMDb ID.

        Args:
            imdb_id: The IMDb ID

        Returns:
            M3U8 URL if found, None otherwise

        Raises:
            URLExtractionError: If extraction fails
        """
        url = self.build_url(imdb_id)
        return await self.extract_from_url(url)

def extract_m3u8_url(imdb_id: str, headless: bool = True) -> Optional[str]:
    """
    Synchronous wrapper for M3U8 URL extraction.

    Args:
        imdb_id: The IMDb ID
        headless: Whether to run browser in headless mode

    Returns:
        M3U8 URL if found, None otherwise
    """
    try:
        extractor = M3U8Extractor(headless=headless)
        return asyncio.run(extractor.extract_from_imdb_id(imdb_id))
    except Exception as e:
        logger.error(f"Failed to extract M3U8 URL: {e}")
        return None

"""M3U8 URL extraction functionality using Playwright."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from .config import (
    NAVIGATION_TIMEOUT, ELEMENT_WAIT_TIMEOUT, CLICK_TIMEOUT, M3U8_REQUEST_TIMEOUT,
    INITIAL_IFRAME_SELECTOR, PLAY_BUTTON_SELECTOR, PLAYER_IFRAME_SELECTOR,
    VIDSRC_BASE_URL
)
import requests
import brotli
import re
from .utils import validate_url, validate_imdb_id, clean_imdb_id

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

    def extract_iframe_url_from_html(self, page_url: str) -> Optional[tuple[str, str]]:
        """
        Extract iframe URL from HTML using HTTP requests (faster and more reliable).
        
        Args:
            page_url: The vidsrc.xyz embed URL
            
        Returns:
            A tuple containing the iframe URL and page title if found, None otherwise
            
        Raises:
            URLExtractionError: If extraction fails
        """
        try:
            logger.info(f"Fetching page source from: {page_url}")
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            response = session.get(page_url, timeout=30)
            
            if response.status_code != 200:
                raise URLExtractionError(f"HTTP error {response.status_code}")
            
            html_content = response.text
            logger.info(f"Retrieved HTML content ({len(html_content)} chars)")
            
            # Extract page title
            title_match = re.search(r'<title>([^<]+)</title>', html_content, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else "Unknown"
            logger.info(f"Page title: {page_title}")
            
            # Look for the player iframe
            iframe_pattern = r'<iframe[^>]+id=["\']player_iframe["\'][^>]+src=["\']([^"\'>]+)["\']'
            iframe_match = re.search(iframe_pattern, html_content, re.IGNORECASE)
            
            if not iframe_match:
                # Try alternative iframe patterns
                iframe_pattern = r'<iframe[^>]+src=["\']([^"\'>]*cloudnestra[^"\'>]*)["\']'
                iframe_match = re.search(iframe_pattern, html_content, re.IGNORECASE)
            
            if not iframe_match:
                raise URLExtractionError("Could not find player iframe in HTML")
            
            iframe_src = iframe_match.group(1)
            
            # Ensure the URL is complete
            if iframe_src.startswith('//'):
                iframe_src = 'https:' + iframe_src
            elif iframe_src.startswith('/'):
                iframe_src = 'https://vidsrc.xyz' + iframe_src
            
            logger.info(f"Found iframe URL: {iframe_src}")
            return iframe_src, page_title
            
        except Exception as e:
            logger.error(f"Error extracting iframe URL: {e}")
            raise URLExtractionError(f"Failed to extract iframe URL: {e}")

    async def extract_from_url(self, page_url: str) -> Optional[tuple[str, str]]:
        """
        Extract M3U8 URL and page title from the given page URL.

        Args:
            page_url: The vidsrc.xyz embed URL

        Returns:
            A tuple containing the M3U8 URL and the page title if found, None otherwise

        Raises:
            URLExtractionError: If extraction fails
        """
        if not validate_url(page_url):
            raise URLExtractionError(f"Invalid URL: {page_url}")

        logger.info(f"Starting M3U8 extraction from: {page_url}")
        
        # First, try to extract iframe URL using HTTP requests (faster)
        try:
            iframe_url, page_title = self.extract_iframe_url_from_html(page_url)
            logger.info(f"Successfully extracted iframe URL: {iframe_url}")
            
            # Now use browser automation to extract M3U8 from the iframe
            return await self.extract_from_iframe(iframe_url, page_title)
            
        except Exception as e:
            logger.warning(f"HTTP extraction failed: {e}, falling back to browser automation")
            return await self.extract_with_browser(page_url)
    
    async def extract_from_iframe(self, iframe_url: str, page_title: str) -> Optional[tuple[str, str]]:
        """
        Extract M3U8 URL from the iframe URL using browser automation.
        
        Args:
            iframe_url: The iframe URL to load
            page_title: The page title
            
        Returns:
            A tuple containing the M3U8 URL and page title if found, None otherwise
        """
        async with async_playwright() as p:
            browser = None
            try:
                # Use Firefox for better compatibility
                browser = await p.firefox.launch(
                    headless=self.headless,
                    firefox_user_prefs={
                        "dom.webdriver.enabled": False,
                        "useAutomationExtension": False,
                    }
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                    viewport={'width': 1366, 'height': 768}
                )
                
                page = await context.new_page()
                
                # Set up M3U8 listener before navigation
                logger.info("Setting up M3U8 request listener...")
                async with page.expect_request("**/*.m3u8", timeout=M3U8_REQUEST_TIMEOUT) as request_info:
                    
                    # Navigate to iframe URL
                    logger.info(f"Navigating to iframe: {iframe_url}")
                    await page.goto(iframe_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT)
                    
                    # Wait for the page to load and try to trigger video playback
                    await page.wait_for_timeout(5000)
                    
                    # Try clicking on the video player area
                    try:
                        await page.click("body", timeout=5000)
                        logger.info("Clicked on page to trigger video")
                    except:
                        logger.info("Could not click on page, assuming autoplay")
                    
                    # Wait for M3U8 request
                    logger.info("Waiting for M3U8 request...")
                    request = await request_info.value
                
                m3u8_url = request.url
                logger.info(f"Successfully extracted M3U8 URL: {m3u8_url}")
                return m3u8_url, page_title
                
            except Exception as e:
                logger.error(f"Error in iframe extraction: {e}")
                raise URLExtractionError(f"Iframe extraction failed: {e}")
            finally:
                if browser:
                    await browser.close()
    
    async def extract_with_browser(self, page_url: str) -> Optional[tuple[str, str]]:
        """
        Fallback method using full browser automation (original approach).
        
        Args:
            page_url: The vidsrc.xyz embed URL
            
        Returns:
            A tuple containing the M3U8 URL and page title if found, None otherwise
        """

        async with async_playwright() as p:
            browser = None
            try:
                # Try Firefox first as it's often less detected
                try:
                    browser = await p.firefox.launch(
                        headless=self.headless,
                        firefox_user_prefs={
                            "dom.webdriver.enabled": False,
                            "useAutomationExtension": False,
                            "general.platform.override": "Win32",
                            "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
                        }
                    )
                    logger.info("Using Firefox browser")
                except Exception as e:
                    logger.warning(f"Firefox launch failed: {e}, falling back to Chromium")
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-extensions',
                            '--no-first-run',
                            '--disable-default-apps',
                            '--disable-background-timer-throttling',
                            '--disable-renderer-backgrounding',
                            '--disable-backgrounding-occluded-windows',
                            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        ]
                    )
                    logger.info("Using Chromium browser")
                
                # Create context with realistic settings
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                    viewport={'width': 1366, 'height': 768},  # More common resolution
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    }
                )
                
                page = await context.new_page()
                
                # Add stealth scripts
                await page.add_init_script("""
                    // Remove webdriver traces
                    delete navigator.__proto__.webdriver;
                    
                    // Mock realistic navigator properties
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            return {
                                0: { name: 'PDF Viewer', filename: 'internal-pdf-viewer' },
                                1: { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                                2: { name: 'Chromium PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                                3: { name: 'Microsoft Edge PDF Viewer', filename: 'pdfjs' },
                                4: { name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer' },
                                length: 5
                            };
                        },
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    // Mock screen properties
                    Object.defineProperty(screen, 'colorDepth', {
                        get: () => 24,
                    });
                    
                    // Add realistic timing
                    const originalDateNow = Date.now;
                    const originalPerformanceNow = performance.now;
                    
                    let startTime = originalDateNow();
                    Date.now = () => originalDateNow() + Math.floor(Math.random() * 10);
                    performance.now = () => originalPerformanceNow() + Math.random();
                """)
                
                # Add a small random delay to seem more human
                await page.wait_for_timeout(1000 + int(2000 * (hash(page_url) % 100) / 100))

                # Navigate with multiple strategies
                response = None
                navigation_successful = False
                
                for attempt in range(3):
                    try:
                        logger.info(f"Navigating to page (attempt {attempt + 1}/3)...")
                        
                        # Add random delay before navigation
                        if attempt > 0:
                            delay = 3000 + (attempt * 2000) + int(1000 * (hash(page_url) % 100) / 100)
                            await page.wait_for_timeout(delay)
                        
                        # Try different navigation strategies
                        if attempt == 0:
                            # First try: simple navigation
                            response = await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                        elif attempt == 1:
                            # Second try: wait for full load
                            response = await page.goto(page_url, wait_until="load", timeout=45000)
                        else:
                            # Third try: wait for network idle and try referer
                            await page.set_extra_http_headers({
                                **context._options.get('extra_http_headers', {}),
                                'Referer': 'https://www.google.com/'
                            })
                            response = await page.goto(page_url, wait_until="networkidle", timeout=60000)
                        
                        # Wait for any redirects or JavaScript execution with random timing
                        wait_time = 2000 + int(2000 * (hash(str(attempt)) % 100) / 100)
                        await page.wait_for_timeout(wait_time)
                        
                        current_url = page.url
                        logger.info(f"Current URL after navigation: {current_url}")
                        
                        # Check if we're still on a blank page or got redirected to an error page
                        if current_url == "about:blank":
                            logger.warning(f"Still on blank page after attempt {attempt + 1}")
                            if attempt < 2:
                                continue
                            else:
                                raise URLExtractionError("Navigation failed - page remains blank")
                        
                        # Check response status if available
                        if response and response.status >= 400:
                            logger.warning(f"HTTP {response.status} on attempt {attempt + 1}")
                            if attempt < 2:
                                continue
                            else:
                                raise URLExtractionError(f"HTTP error {response.status}: {response.status_text}")
                        
                        # Check if we got redirected to a blocking page
                        if "blocked" in current_url.lower() or "error" in current_url.lower():
                            logger.warning(f"Redirected to blocking page: {current_url}")
                            if attempt < 2:
                                continue
                            else:
                                raise URLExtractionError(f"Redirected to blocking page: {current_url}")
                        
                        logger.info(f"Navigation successful to: {current_url}")
                        navigation_successful = True
                        break
                        
                    except PlaywrightTimeoutError as e:
                        logger.warning(f"Navigation timeout on attempt {attempt + 1}: {e}")
                        if attempt == 2:
                            raise URLExtractionError(f"Navigation timeout after 3 attempts")
                        await asyncio.sleep(5)
                    except Exception as e:
                        logger.warning(f"Navigation error on attempt {attempt + 1}: {e}")
                        if attempt == 2:
                            raise URLExtractionError(f"Navigation failed after 3 attempts: {e}")
                        await asyncio.sleep(5)
                
                if not navigation_successful:
                    raise URLExtractionError("Failed to navigate to the page after all attempts")

                # Get page information
                page_title = await page.title()
                final_url = page.url
                logger.info(f"Page title: '{page_title}'")
                logger.info(f"Final page URL: {final_url}")
                
                # Get page content for analysis
                page_content = await page.content()
                logger.info(f"Page content length: {len(page_content)} characters")
                
                # Check for blocking indicators
                content_lower = page_content.lower()
                blocking_indicators = ['blocked', 'access denied', 'forbidden', 'not available', 'error 403', 'error 404']
                for indicator in blocking_indicators:
                    if indicator in content_lower:
                        logger.error(f"Blocking indicator found: '{indicator}'")
                        raise URLExtractionError(f"Site blocking detected: {indicator}")
                
                # Check if page is mostly empty (potential blocking)
                if len(page_content.strip()) < 100:
                    logger.error(f"Page content too short: {len(page_content)} chars")
                    raise URLExtractionError("Page appears to be empty or blocked")
                
                # Wait for page to fully load
                await page.wait_for_load_state("networkidle")
                
                # Look for iframes with better error handling
                logger.info("Locating initial iframe...")
                iframe_count = await page.evaluate("document.querySelectorAll('iframe').length")
                logger.info(f"Found {iframe_count} iframe(s) on the page")
                
                if iframe_count == 0:
                    logger.info("No iframes found immediately, waiting for dynamic content...")
                    await page.wait_for_timeout(10000)  # Wait longer for dynamic content
                    iframe_count = await page.evaluate("document.querySelectorAll('iframe').length")
                    logger.info(f"After waiting: Found {iframe_count} iframe(s)")
                    
                    if iframe_count == 0:
                        # Log page content for debugging
                        content_preview = page_content[:2000] if len(page_content) > 2000 else page_content
                        logger.error(f"No iframes found. Page content preview: {content_preview}")
                        
                        # Check if this is a different type of page structure
                        if "vidsrc" in content_lower and ("video" in content_lower or "player" in content_lower):
                            logger.info("Page contains video-related content but no iframes - site structure may have changed")
                        
                        raise URLExtractionError("No iframes found - site structure may have changed or content is blocked")
                
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
                return m3u8_url, page_title

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

    async def extract_from_imdb_id(self, imdb_id: str) -> Optional[tuple[str, str]]:
        """
        Extract M3U8 URL using IMDb ID.

        Args:
            imdb_id: The IMDb ID

        Returns:
            A tuple containing the M3U8 URL and the page title if found, None otherwise

        Raises:
            URLExtractionError: If extraction fails
        """
        url = self.build_url(imdb_id)
        return await self.extract_from_url(url)

def extract_m3u8_url(imdb_id: str, headless: bool = True) -> Optional[tuple[str, str]]:
    """
    Synchronous wrapper for M3U8 URL extraction.

    Args:
        imdb_id: The IMDb ID
        headless: Whether to run browser in headless mode

    Returns:
        A tuple containing the M3U8 URL and the page title if found, None otherwise
    """
    try:
        extractor = M3U8Extractor(headless=headless)
        return asyncio.run(extractor.extract_from_imdb_id(imdb_id))
    except Exception as e:
        logger.error(f"Failed to extract M3U8 URL: {e}")
        return None

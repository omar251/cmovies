# Troubleshooting Guide

## Issue: Iframe Timeout Error

### Problem
```
ERROR - Timeout during extraction: Page.wait_for_selector: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("iframe") to be visible
```

### Root Causes & Solutions

#### 1. **Dependencies Not Installed**
**Symptoms**: `ModuleNotFoundError: No module named 'imdb'` or `No module named 'playwright'`

**Solution**:
```bash
# Install dependencies
uv sync
playwright install chromium

# Or manually:
pip install imdbpy playwright pyfzf requests
playwright install chromium
```

#### 2. **Website Structure Changed**
**Symptoms**: No iframes found on the page

**Solutions**:
- Run with visible browser to inspect: `python cli.py --imdb-id tt0133093 --no-headless`
- Use the debug script: `python simple_test.py`
- Check if selectors need updating in `config.py`

#### 3. **Anti-Bot Detection**
**Symptoms**: Page loads but no content, or different content than expected

**Solutions Applied**:
- ✅ Added realistic User-Agent
- ✅ Disabled automation detection flags
- ✅ Increased timeouts
- ✅ Added random delays

#### 4. **Network/Loading Issues**
**Symptoms**: Timeouts during page load or element waiting

**Solutions**:
- Increased timeouts in `config.py`:
  - `NAVIGATION_TIMEOUT = 45000` (45 seconds)
  - `ELEMENT_WAIT_TIMEOUT = 20000` (20 seconds)
  - `M3U8_REQUEST_TIMEOUT = 60000` (60 seconds)

### Debug Steps

#### Step 1: Install Dependencies
```bash
python install_deps.py
```

#### Step 2: Test with Visible Browser
```bash
python simple_test.py
```
This will:
- Open a visible browser window
- Navigate to the vidsrc.xyz page
- Show you exactly what's happening
- Report iframe count and details

#### Step 3: Run Full Extraction with Debug
```bash
python cli.py --imdb-id tt0133093 --no-headless --verbose
```

#### Step 4: Check Configuration
If the website structure changed, update selectors in `config.py`:
```python
# Current selectors
INITIAL_IFRAME_SELECTOR = "iframe"
PLAY_BUTTON_SELECTOR = "#pl_but_background"
PLAYER_IFRAME_SELECTOR = 'iframe[id="player_iframe"]'
```

### Common Fixes

#### Fix 1: Update Selectors
If the debug shows different iframe structure, update `config.py`:
```python
# Example: if iframe has a specific class
INITIAL_IFRAME_SELECTOR = "iframe.video-frame"
```

#### Fix 2: Add More Wait Time
If the page loads slowly, increase timeouts:
```python
ELEMENT_WAIT_TIMEOUT = 30000  # 30 seconds
```

#### Fix 3: Handle Dynamic Loading
The improved code now:
- Waits for DOM content to load
- Checks iframe count multiple times
- Adds delays for dynamic content

### Testing Different Movies

Try different IMDb IDs to see if it's movie-specific:
```bash
python cli.py --imdb-id tt0111161  # The Shawshank Redemption
python cli.py --imdb-id tt0068646  # The Godfather
python cli.py --imdb-id tt0468569  # The Dark Knight
```

### Manual Browser Test

1. Open browser manually
2. Go to: `https://vidsrc.xyz/embed/movie/0133093`
3. Check if:
   - Page loads correctly
   - Iframes are present
   - Play button exists
   - Video player appears after clicking

### Next Steps if Still Failing

1. **Check Website Status**: Visit vidsrc.xyz manually
2. **Update Selectors**: Use browser dev tools to find current selectors
3. **Try Different Movies**: Some movies might not be available
4. **Check Network**: Ensure no firewall/proxy blocking
5. **Update Browser**: `playwright install chromium --force`

### Success Indicators

When working correctly, you should see:
```
INFO - Built URL: https://vidsrc.xyz/embed/movie/0133093 (from IMDb ID: tt0133093)
INFO - Starting M3U8 extraction from: https://vidsrc.xyz/embed/movie/0133093
INFO - Navigating to page...
INFO - Page title: [Page Title]
INFO - Found 1 iframe(s) on the page
INFO - Looking for play button...
INFO - Clicking play button...
INFO - Waiting for player iframe...
INFO - Successfully extracted M3U8 URL: [URL]
```
# M3U8 URL Extractor for vidsrc.xyz

This script is designed to extract the M3U8 video stream URL from a `vidsrc.xyz` embed page. It uses Playwright to automate a headless browser and capture the network requests that reveal the final video stream.

## The Challenge

The target website, `vidsrc.xyz`, employs a multi-step process to protect its video streams. A simple `GET` request is not enough to get the M3U8 URL. The script needs to simulate a real user's actions to trigger the video player and reveal the stream.

The process involves:

1.  **Initial Page Load:** The first page loads an `iframe` that contains a poster of the movie and a play button.
2.  **First Click:** The user must click the play button (or the poster itself) to trigger the next step.
3.  **Second Iframe:** After the first click, a *second* `iframe` is dynamically created. This new iframe contains the actual video player.
4.  **Video Player:** The video player in the second iframe may autoplay, or it may require another click to start.
5.  **M3U8 Request:** The M3U8 URL is only requested when the video player in the second iframe begins to play.

## The Solution

This script automates the entire process:

1.  **Launches Playwright:** It starts a headless Chromium browser.
2.  **Navigates to the Page:** It loads the initial `vidsrc.xyz` embed URL.
3.  **Finds the First Iframe:** It locates the first `iframe` on the page.
4.  **Listens for M3U8:** It sets up a listener to intercept any network requests for files ending in `.m3u8`.
5.  **Clicks the Play Button:** It uses a JavaScript-based click to simulate a user clicking the play button. This was a key step, as a standard Playwright click was not always effective.
6.  **Waits for the Second Iframe:** It waits for the second `iframe` (with the ID `player_iframe`) to be created.
7.  **Interacts with the Player:** It clicks inside the second `iframe` to ensure the video starts playing.
8.  **Captures the URL:** The M3U8 listener captures the URL of the video stream.
9.  **Returns the URL:** The script prints the final M3U8 URL to the console.

This multi-step, carefully sequenced approach allows the script to successfully navigate the site's protections and extract the video stream URL.

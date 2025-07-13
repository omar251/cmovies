#!/usr/bin/env python3
"""Debug script to test the extraction with visible browser."""

import asyncio
from url_extractor import M3U8Extractor

async def debug_extraction():
    """Run extraction with visible browser for debugging."""
    
    # Test with The Matrix IMDb ID
    imdb_id = "tt0133093"
    
    print(f"Testing extraction for IMDb ID: {imdb_id}")
    print("Running with visible browser for debugging...")
    
    try:
        # Create extractor with visible browser
        extractor = M3U8Extractor(headless=False)
        
        # Build URL
        url = extractor.build_url(imdb_id)
        print(f"Target URL: {url}")
        
        # Extract M3U8 URL
        m3u8_url = await extractor.extract_from_imdb_id(imdb_id)
        
        if m3u8_url:
            print(f"✅ Successfully extracted M3U8 URL: {m3u8_url}")
        else:
            print("❌ Failed to extract M3U8 URL")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    print("Debug M3U8 Extraction")
    print("=" * 30)
    asyncio.run(debug_extraction())
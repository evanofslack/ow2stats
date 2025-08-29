#!/usr/bin/env python3
"""
Test the updated scraper with text parsing
"""

import sys
from pathlib import Path
from scrape import OverwatchScraper


def test_text_parsing():
    """Test the text parsing functionality directly"""

    # Create scraper instance
    scraper = OverwatchScraper("config_debug.json")

    # Sample text that matches what we saw in the diagnostic
    sample_text = """
HERO STATISTICS
ROLE
ALL
TANK
DAMAGE
SUPPORT
Genji 12.5% 48.2%
Hanzo 8.3% 51.7%
Tracer 15.2% 49.8%
Mercy 25.1% 58.2%
Reinhardt 18.7% 52.4%
"""

    print("🧪 TESTING TEXT PARSING")
    print("=" * 40)

    # Test the parsing function
    hero_data = scraper._parse_hero_data_from_text(sample_text)

    if hero_data:
        print(f"✅ Found {len(hero_data)} heroes in sample text:")
        for hero in hero_data:
            print(
                f"  - {hero['hero']}: Pick {hero['pick_rate']}, Win {hero['win_rate']}"
            )
    else:
        print("❌ No heroes found in sample text")

    return len(hero_data) > 0


def test_live_scraping():
    """Test scraping the actual page"""

    print("\n🌐 TESTING LIVE SCRAPING")
    print("=" * 40)

    # Create scraper with debug config
    config = {
        "timeout": 30,
        "headless": False,  # Keep visible for debugging
        "debug_mode": True,
        "regions": ["Americas"],
        "platforms": ["PC"],
        "roles": ["All"],
    }

    # Save debug config
    import json

    with open("test_config.json", "w") as f:
        json.dump(config, f, indent=2)

    scraper = OverwatchScraper("test_config.json")

    try:
        print("🔄 Attempting to scrape...")
        stats = scraper._scrape_stats_page("PC", "Americas", "All", "Quick Play", "All")

        if stats:
            print(f"✅ SUCCESS! Found {len(stats)} heroes:")
            for stat in stats[:10]:  # Show first 10
                pick = f"{stat.pick_rate}%" if stat.pick_rate else "N/A"
                win = f"{stat.win_rate}%" if stat.win_rate else "N/A"
                print(f"  - {stat.hero}: Pick {pick}, Win {win}")

            # Save to database
            scraper._save_stats(stats)
            print(f"💾 Saved {len(stats)} stats to database")

        else:
            print("❌ No stats found")
            print("Check the debug folder for HTML files")

    except Exception as e:
        print(f"💥 Error during scraping: {e}")
        import traceback

        traceback.print_exc()


def main():
    print("🚀 OVERWATCH SCRAPER TEST")
    print("=" * 50)

    # Test 1: Text parsing
    parsing_works = test_text_parsing()

    # Test 2: Live scraping (only if parsing works)
    if parsing_works:
        test_live_scraping()
    else:
        print("⏭️  Skipping live test - text parsing failed")

    print("\n🏁 Test completed!")


if __name__ == "__main__":
    main()

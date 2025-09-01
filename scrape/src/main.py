import sys

from .scrape import OverwatchScraper


def main():
    """Main execution function."""
    scraper = OverwatchScraper()
    try:
        scraper.logger.info("Starting Overwatch statistics scraping")
        scraper.scrape_all_configurations()
    except KeyboardInterrupt:
        scraper.logger.info("Scraping interrupted by user")
    except Exception as e:
        scraper.logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

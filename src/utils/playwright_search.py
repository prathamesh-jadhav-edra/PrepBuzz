"""Playwright-based Google search functionality for better reliability."""

import asyncio
import random
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from loguru import logger

try:
    from playwright.async_api import (
        async_playwright,
        TimeoutError as PlaywrightTimeoutError,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright")


class PlaywrightSearcher:
    """Playwright-based search scraper for better reliability."""

    def __init__(self):
        """Initialize the searcher."""
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]

    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Google using Playwright.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of search results with title, url, and snippet
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return []

        logger.info(f"Playwright searching Google for: {query}")

        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--no-first-run",
                        "--disable-default-apps",
                        "--disable-extensions",
                    ],
                )

                # Create new page with random user agent
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1920, "height": 1080},
                )
                page = await context.new_page()

                # Navigate to Google search
                encoded_query = quote_plus(query)
                search_url = (
                    f"https://www.google.com/search?q={encoded_query}&num={num_results}"
                )

                await page.goto(search_url, wait_until="networkidle", timeout=10000)

                # Wait for search results to load
                try:
                    await page.wait_for_selector(
                        "[data-sokoban-container]", timeout=5000
                    )
                except PlaywrightTimeoutError:
                    # Try alternative selector
                    try:
                        await page.wait_for_selector('div[class*="g"]', timeout=5000)
                    except PlaywrightTimeoutError:
                        logger.warning(
                            "Search results not found with expected selectors"
                        )

                # Extract search results
                results = []

                # Try multiple selectors for search result containers
                search_selectors = [
                    "div[data-sokoban-container] div.g",
                    "div.g",
                    "div.tF2Cxc",
                    "div.MjjYud",
                    "[data-sokoban-container] > div",
                ]

                search_elements = None
                for selector in search_selectors:
                    try:
                        search_elements = await page.query_selector_all(selector)
                        if search_elements:
                            logger.debug(
                                f"Found {len(search_elements)} results with selector: {selector}"
                            )
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if not search_elements:
                    logger.warning("No search results found with any selector")
                    await browser.close()
                    return []

                # Process each result
                for element in search_elements[:num_results]:
                    try:
                        # Extract title
                        title_elem = await element.query_selector("h3")
                        title = ""
                        if title_elem:
                            title = await title_elem.text_content()

                        # Extract URL
                        link_elem = await element.query_selector('a[href^="http"]')
                        url = ""
                        if link_elem:
                            url = await link_elem.get_attribute("href")

                        # Extract snippet/description
                        snippet = ""
                        snippet_selectors = [
                            '[data-sncf="1"] span',
                            ".VwiC3b",
                            ".IsZvec",
                            ".aCOpRe",
                            ".st",
                        ]

                        for snippet_sel in snippet_selectors:
                            snippet_elem = await element.query_selector(snippet_sel)
                            if snippet_elem:
                                snippet = await snippet_elem.text_content()
                                if snippet:
                                    break

                        # Add result if we have title and URL
                        if title and url and url.startswith("http"):
                            results.append(
                                {
                                    "title": title.strip(),
                                    "url": url,
                                    "snippet": snippet.strip() if snippet else "",
                                }
                            )
                            logger.debug(f"Found result: {title[:50]}...")

                    except Exception as e:
                        logger.warning(f"Error processing search result: {e}")
                        continue

                await browser.close()
                logger.info(f"Playwright found {len(results)} search results")
                return results

        except Exception as e:
            logger.error(f"Playwright search failed: {e}")
            return []

    def search_sync(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Synchronous wrapper for the async search method.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of search results
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.search(query, num_results))

    def search_cat_question_context(
        self, question: str, subject: str
    ) -> List[Dict[str, str]]:
        """
        Search for context related to a CAT question using Playwright.

        Args:
            question: The CAT question text
            subject: Question subject (Quant, Verbal, Logic, DI)

        Returns:
            List of relevant search results
        """
        # Create focused search queries for CAT context
        search_queries = [
            f"CAT {subject} {question[:50]} solution",
            f"CAT exam {subject} explanation approach",
        ]

        all_results = []

        for query in search_queries:
            try:
                results = self.search_sync(query, num_results=3)
                all_results.extend(results)

                # Add delay between queries
                import time

                time.sleep(random.uniform(2, 4))

            except Exception as e:
                logger.error(f"Error searching for query '{query}': {e}")
                continue

        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)

        return unique_results[:5]  # Return top 5 unique results


# Global playwright searcher instance
playwright_searcher = PlaywrightSearcher()

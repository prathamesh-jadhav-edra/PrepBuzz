"""Google search functionality without API using web scraping."""

import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote_plus
from typing import List, Dict, Optional
from loguru import logger

try:
    from .playwright_search import playwright_searcher
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright searcher not available, falling back to requests")


class GoogleSearcher:
    """Simple Google search scraper without API."""
    
    def __init__(self):
        """Initialize the searcher with user agents."""
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        ]
        
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Google for the given query.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per page)
            
        Returns:
            List of search results with title, url, and snippet
        """
        # Try Playwright first if available (more reliable)
        if PLAYWRIGHT_AVAILABLE:
            try:
                logger.info("Using Playwright for Google search")
                results = playwright_searcher.search_sync(query, num_results)
                if results:
                    return results
                logger.warning("Playwright search returned no results, falling back to requests")
            except Exception as e:
                logger.warning(f"Playwright search failed: {e}, falling back to requests")
        
        # Fallback to requests + BeautifulSoup
        logger.info(f"Using requests fallback for Google search: {query}")
        
        try:
            # Encode query for URL
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
            
            # Add random delay to avoid being flagged
            time.sleep(random.uniform(0.5, 1.5))
            
            # Make request with randomized headers
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            
            # Debug: Print some of the HTML to understand structure
            if not soup.find_all('div', class_='g'):
                logger.debug("No 'div.g' containers found, trying alternative selectors")
                # Print first few divs to debug structure
                divs = soup.find_all('div')[:10]
                logger.debug(f"Found {len(divs)} div elements in total")
            
            # Try multiple selectors (Google frequently changes these)
            search_containers = (
                soup.find_all('div', class_='g') or 
                soup.find_all('div', class_='tF2Cxc') or
                soup.find_all('div', class_='MjjYud') or
                soup.find_all('div', class_='Gx5Zad')
            )
            
            if not search_containers:
                # Last resort: look for any div with an h3 inside
                search_containers = soup.find_all('div', lambda value: value and 'result' in value.lower())
                if not search_containers:
                    # Find any div that contains an h3 and an a tag
                    all_divs = soup.find_all('div')
                    search_containers = [div for div in all_divs if div.find('h3') and div.find('a')]
            
            logger.debug(f"Found {len(search_containers)} potential result containers")
            
            for container in search_containers[:num_results]:
                try:
                    # Extract title and URL - try multiple approaches
                    title_elem = container.find('h3')
                    link_elem = None
                    
                    if title_elem:
                        # Find the associated link
                        link_elem = title_elem.find_parent('a')
                        if not link_elem:
                            # Look for sibling or nearby a tag
                            link_elem = title_elem.find_previous('a') or title_elem.find_next('a')
                        if not link_elem:
                            # Look anywhere in the container
                            link_elem = container.find('a', href=True)
                    
                    if not title_elem or not link_elem:
                        # Try finding any a tag with href
                        link_elem = container.find('a', href=True)
                        if link_elem:
                            title_elem = link_elem.find('h3') or link_elem
                    
                    if title_elem and link_elem and link_elem.get('href'):
                        title = title_elem.get_text(strip=True)
                        url = link_elem['href']
                        
                        # Clean up URL (remove Google redirect)
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        # Extract snippet/description - try multiple selectors
                        snippet = ""
                        snippet_selectors = [
                            'span.aCOpRe', 'span.st', 'div.IsZvec', 'div.VwiC3b', 
                            'div.s', 'span.a3xZa', 'div.BNeawe.s3v9rd.AP7Wnd'
                        ]
                        
                        for selector in snippet_selectors:
                            snippet_elem = container.select_one(selector)
                            if snippet_elem:
                                snippet = snippet_elem.get_text(strip=True)
                                break
                        
                        if title and url.startswith('http'):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            logger.debug(f"Found result: {title[:50]}...")
                            
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Found {len(results)} search results")
            
            # If Google search failed, try DuckDuckGo as fallback
            if not results:
                logger.info("Google search returned no results, trying DuckDuckGo fallback")
                return self._search_duckduckgo(query, num_results)
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Google search request failed: {e}")
            # Try DuckDuckGo as fallback
            return self._search_duckduckgo(query, num_results)
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Fallback search using DuckDuckGo (less likely to block).
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # DuckDuckGo search URL
            url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            # Add delay
            time.sleep(random.uniform(0.5, 1.0))
            
            # Make request
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            # DuckDuckGo result selectors
            search_containers = soup.find_all('div', class_='result') or soup.find_all('div', class_='web-result')
            
            for container in search_containers[:num_results]:
                try:
                    # Extract title and URL
                    title_elem = container.find('h2') or container.find('a', class_='result__a')
                    link_elem = container.find('a', class_='result__url') or container.find('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        
                        # Extract snippet
                        snippet = ""
                        snippet_elem = container.find('div', class_='result__snippet') or \
                                      container.find('span', class_='result__snippet')
                        if snippet_elem:
                            snippet = snippet_elem.get_text(strip=True)
                        
                        if title and url.startswith('http'):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            
                except Exception as e:
                    logger.warning(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
            logger.info(f"DuckDuckGo found {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def search_cat_question_context(self, question: str, subject: str) -> List[Dict[str, str]]:
        """
        Search for context related to a CAT question.
        
        Args:
            question: The CAT question text
            subject: Question subject (Quant, Verbal, Logic, DI)
            
        Returns:
            List of relevant search results
        """
        # Create focused search queries for CAT context
        search_queries = [
            f"CAT {subject} {question[:50]}",
            f"CAT exam {subject} solution explanation",
            f"CAT {subject} problem solving technique",
        ]
        
        all_results = []
        
        for query in search_queries:
            results = self.search(query, num_results=3)
            all_results.extend(results)
            
            # Add delay between queries
            time.sleep(random.uniform(1, 2))
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results[:5]  # Return top 5 unique results


# Global searcher instance
google_searcher = GoogleSearcher()
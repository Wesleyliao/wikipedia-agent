"""Wikipedia search tool for the agent."""

import requests

WIKIPEDIA_TOOL_SCHEMA = {
    "name": "search_wikipedia",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on Wikipedia.",
            }
        },
        "required": ["query"],
    },
}


def build_tool_definition(descriptions: dict[str, str]) -> dict:
    """Build the Anthropic tool definition with the given description."""
    return {**WIKIPEDIA_TOOL_SCHEMA, "description": descriptions["search_wikipedia"]}


def search_wikipedia(query: str, num_results: int = 3) -> str:
    """Search Wikipedia and return plain-text summaries of top results.

    Uses the MediaWiki API action=query with list=search to find pages,
    then fetches extracts for the top results.
    """
    api_url = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "WikipediaAgent/1.0"}

    # Step 1: Search for page titles
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": num_results,
        "format": "json",
    }
    resp = requests.get(api_url, params=search_params, headers=headers, timeout=10)
    resp.raise_for_status()
    search_results = resp.json().get("query", {}).get("search", [])

    if not search_results:
        return f"No Wikipedia articles found for: {query}"

    # Step 2: Fetch extracts for found pages
    titles = [r["title"] for r in search_results]
    extract_params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "format": "json",
    }
    resp = requests.get(api_url, params=extract_params, headers=headers, timeout=10)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", {})

    # Step 3: Format results
    results = []
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        title = page.get("title", "Unknown")
        extract = page.get("extract", "No summary available.")
        if len(extract) > 1000:
            extract = extract[:1000] + "..."
        results.append(f"## {title}\n{extract}")

    if not results:
        return f"No Wikipedia articles found for: {query}"

    return "\n\n---\n\n".join(results)


TOOL_MAP = {
    "search_wikipedia": search_wikipedia,
}

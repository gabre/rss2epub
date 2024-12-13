"""
This script fetches and parses an RSS feed and prints out the
feed title, its link and the titles, links and summaries of all
articles in the feed.
"""
from feedparser.util import FeedParserDict
import feedparser
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rss_url", type=str, help="url of the RSS feed")
    args = parser.parse_args()
    rss_url = args.rss_url
    for entry in fetch_all_entries(rss_url):
        print(f"Title: {entry.title}")
        print(f"Link: {entry.link}")
        print(f"Published: {entry.published if 'published' in entry else 'N/A'}")
        print(f"Summary: {entry.summary if 'summary' in entry else 'N/A'}\n")

def fetch_all_entries(rss_url):
    pageNumber = 1
    hasMorePages = True
    all_entries = []
    while hasMorePages:
        next_url = f"{rss_url}?paged={pageNumber}"
        feed: FeedParserDict = feedparser.parse(next_url)
        if feed.bozo:
            raise feed.bozo_exception
        all_entries += feed.entries
        hasMorePages = len(feed.entries) > 0
        pageNumber += 1
    return reversed(all_entries)

if __name__ == "__main__":
    main()

from feedparser.util import FeedParserDict
import feedparser
import argparse
import pickle
import os
from jinja2 import Environment, FileSystemLoader
from ebooklib import epub


DEFAULT_TITLE = 'Untitled'
CACHE_FILE = '.book-cache'
HTML_JINJA_TEMPLATE = 'template.html'
HTML_OUTPUT_FILENAME = 'articles.html'
EPUB_OUTPUT_FILENAME = 'articles.epub'
CHAPTER_JINJA_TEMPLATE = 'chapter.html'


class Article:
    def __init__(self, title: str, categories: list[str], published: str,
                 link: str, summary: str, content: str):
        self.title = title
        self.categories = [categories]
        self.published = published
        self.link = link
        self.summary = summary
        self.content = content


class Book:
    def __init__(self, title: str, articles: list[Article]):
        self.title = title
        self.articles = articles


def get_preferred_content(self: FeedParserDict) -> str:
    if 'content' in self:
        for content in self['content']:
            if content['type'] == 'text/html':
                return str(content['value'])

        return str(self['content'][0]['value'])
    return ""


feedparser.FeedParserDict.get_preferred_content = get_preferred_content


def entry_to_article(self: FeedParserDict) -> Article:
    return Article(
        title=self.title,
        categories=self.category,
        published=self.published if 'published' in self else 'N/A',
        link=self.link,
        summary=self.summary if 'summary' in self else 'N/A',
        content=self.get_preferred_content(),
    )


def fetch_all_entries(rss_url: str) -> Book:
    pageNumber = 1
    hasMorePages = True
    all_entries = []
    title = DEFAULT_TITLE
    while hasMorePages:
        next_url = f"{rss_url}?paged={pageNumber}"
        feed: FeedParserDict = feedparser.parse(next_url)
        if feed.bozo:
            raise Exception(
                f"Failed to fetch the feed. Error: {feed.bozo_exception}"
                )
        if title == DEFAULT_TITLE:
            title = feed.feed.title
        all_entries += [entry_to_article(entry) for entry in feed.entries]
        hasMorePages = len(feed.entries) > 0
        pageNumber += 1
    corrected_title = correct_title(title)
    return Book(
        corrected_title,
        list(reversed(all_entries))
        )


def remove_cache():
    if exists_cache():
        os.remove(CACHE_FILE)


def save_cache(book: Book):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(book, f)


def load_cache():
    with open(CACHE_FILE, 'rb') as f:
        return pickle.load(f)


def exists_cache():
    return os.path.exists(CACHE_FILE)


def get_book(rss_url: str, re_cache: bool) -> Book:
    if re_cache:
        remove_cache()
    if exists_cache():
        return load_cache()
    else:
        book = fetch_all_entries(rss_url)
        save_cache(book)
        return book


def render_html(book: Book) -> str:
    return Environment(loader=FileSystemLoader('.')) \
        .get_template(HTML_JINJA_TEMPLATE) \
        .render(book=book)


def write_html(book: Book, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(render_html(book))


def write_epub(book: Book, filename: str):
    ebook = epub.EpubBook()
    ebook.set_title(book.title)

    chapter_template = Environment(loader=FileSystemLoader('.')) \
        .get_template(CHAPTER_JINJA_TEMPLATE)
    epub_chapters = []
    for i, article in enumerate(book.articles, 1):
        chapter = epub.EpubHtml(
            title=article.title,
            file_name=f'chapter_{i}.xhtml',
            lang='hu'
            )
        chapter.content = chapter_template.render(article=article)
        ebook.add_item(chapter)
        epub_chapters.append(chapter)

    ebook.toc = tuple(epub_chapters)
    ebook.spine = ['nav'] + epub_chapters
    ebook.add_item(epub.EpubNcx())
    ebook.add_item(epub.EpubNav())
    epub.write_epub(filename, ebook)


def is_repeated_substring_twice(s: str) -> bool:
    if len(s) % 2 != 0:
        return False
    half_length = len(s) // 2
    return s[:half_length] == s[half_length:]


def correct_title(title: str) -> str:
    if is_repeated_substring_twice(title):
        return title[:len(title) // 2]
    return title


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rss_url", type=str, help="url of the RSS feed")
    parser.add_argument('-r', '--re_cache', action='store_true',
                        help="delete/refill the cache")
    parser.add_argument(
        "mode",
        choices=["html", "epub"],
        default="html",
        nargs="?",
        help="Choose the mode: 'html' (default) or 'epub' output"
    )
    args = parser.parse_args()

    book = get_book(args.rss_url, args.re_cache)
    if args.mode == "html":
        write_html(book, HTML_OUTPUT_FILENAME)
    else:
        write_epub(book, EPUB_OUTPUT_FILENAME)


if __name__ == "__main__":
    main()

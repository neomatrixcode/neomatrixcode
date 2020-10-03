from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os

root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")


TOKEN = os.environ.get("API_TOKEN_GITHUB", "")


def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def fetch_blog_entries():
    entries = feedparser.parse("https://medium.com/feed/@josueacevedo")["entries"]
    return [
        {
            "title": entry["title"].replace(" ", "%20"),
            "subtitle": re.search('<p>.*?</p>',entry['summary'], re.IGNORECASE).group(0).replace("<p>", "").replace("</p>", "").replace(" ", "%20"),
            "url": entry["link"],
            "published": entry["updated"].split("T")[0],
        }
        for entry in entries
    ]

def fetch_videos_entries():
    entries = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UCv1jJ5-lNVvOz3aBqmuC8Rw")["entries"]
    return [
        {
            "title": entry["title"].replace(" ", "%20"),
            "url": entry["link"],
            "published": entry["updated"].split("T")[0],
        }
        for entry in entries
    ]

def fetch_audios_entries():
    entries = feedparser.parse("https://anchor.fm/s/1acd0770/podcast/rss")["entries"]
    return [
        {
            "title": entry["title"].replace(" ", "%20"),
            "url": entry["link"],
            "published": str(feedparser.parse("https://anchor.fm/s/1acd0770/podcast/rss")["entries"][0]["published_parsed"].tm_year) +"-"+str(feedparser.parse("https://anchor.fm/s/1acd0770/podcast/rss")["entries"][0]["published_parsed"].tm_mon)+"-"+str(feedparser.parse("https://anchor.fm/s/1acd0770/podcast/rss")["entries"][0]["published_parsed"].tm_mday),
        }
        for entry in entries
    ]

if __name__ == "__main__":
    readme = root / "README.md"
    project_releases = root / "releases.md"

    entries = fetch_blog_entries()[:4]
    entries_md = "\n\n".join(
        ["<a href=\"{url}\"><img align=\"left\" src=\"https://github-readme-items.herokuapp.com/medium-item?date={published}&title={title}&subtitle={subtitle}\" /></a>".format(**entry) for entry in entries]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "blog", entries_md)

    readme.open("w").write(rewritten)

    videos = fetch_videos_entries()[:4]
    videos_md = "\n\n".join(
        ["<a href=\"{url}\"><img align=\"left\" src=\"https://github-readme-items.herokuapp.com/youtube-item?date={published}&title={title}\" /></a>".format(**entry) for entry in videos]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "youtube", videos_md)

    readme.open("w").write(rewritten)

    audios = fetch_audios_entries()[:4]
    audios_md = "\n\n".join(
        ["<a href=\"{url}\"><img align=\"left\" src=\"https://github-readme-items.herokuapp.com/anchor-item?date={published}&title={title}\" /></a>".format(**entry) for entry in audios]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "podcast", audios_md)

    readme.open("w").write(rewritten)

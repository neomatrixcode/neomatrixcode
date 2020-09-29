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


def make_query(after_cursor=None, include_organization=False):
    return """
query {
  repositoryOwner(login: "codeneomatrix"){
    repositories(first: 3, isFork:false , privacy: PUBLIC, orderBy:{field:STARGAZERS direction:DESC} ){
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes{
        name
        description
        url
        releases(last:1){
          totalCount
          nodes{
            name
            publishedAt
            url
          }
        }

      }
    }
  }
}
"""

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


if __name__ == "__main__":
    readme = root / "README.md"
    project_releases = root / "releases.md"


    entries = fetch_blog_entries()[:5]
    entries_md = "\n\n".join(
        ["<a href=\"{url}\"><img align=\"left\" src=\"https://github-readme-items.herokuapp.com/medium-item?date={published}&title={title}&subtitle={subtitle}\" /></a>".format(**entry) for entry in entries]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "blog", entries_md)

    readme.open("w").write(rewritten)

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


def fetch_releases(oauth_token):
    repos = []
    releases = []
    repo_names = set()
    has_next_page = True
    after_cursor = None

    first = True

    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor, include_organization=first),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )
        first = False
        print()
        print(json.dumps(data, indent=4))
        print()
        repo_nodes = data["data"]["repositoryOwner"]["repositories"]["nodes"]
        if "organization" in data["data"]:
            repo_nodes += data["data"]["organization"]["repositories"]["nodes"]
        for repo in repo_nodes:
            if repo["name"] not in repo_names:
                repos.append(repo)
                repo_names.add(repo["name"])
                releases.append(
                    {
                        "repo": repo["name"],
                        "repo_url": repo["url"],
                        "publishedAt": repo["releases"]["nodes"][0]["publishedAt"],
                        "release": repo["releases"]["nodes"][0]["name"]
                        .replace(repo["name"], "")
                        .strip(),
                        "url": repo["releases"]["nodes"][0]["url"],
                    }
                )
        has_next_page = False
    return releases


def fetch_blog_entries():
    entries = feedparser.parse("https://medium.com/feed/@josueacevedo")["channel"]
    return [
        {
            "title": entry["item"]["title"],
            "url": entry["item"]["link"].split("#")[0],
            "published": entry["item"]["pubDate"],
        }
        for entry in entries
    ]


if __name__ == "__main__":
    readme = root / "README.md"
    project_releases = root / "releases.md"
    releases = fetch_releases(TOKEN)
    releases.sort(key=lambda r: r["name"], reverse=True)
    md = "\n\n".join(
        [
            "[{repo} {release}]({url}) - {publishedAt}".format(**release)
            for release in releases[:8]
        ]
    )
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "recent_releases", md)

    # tils = fetch_tils()
    # tils_md = "\n\n".join(
    #     [
    #         "[{title}]({url}) - {created_at}".format(
    #             title=til["title"],
    #             url=til["url"],
    #             created_at=til["created_utc"].split("T")[0],
    #         )
    #         for til in tils
    #     ]
    # )
    # rewritten = replace_chunk(rewritten, "tils", tils_md)

    # entries = fetch_blog_entries()[:5]
    # entries_md = "\n\n".join(
    #     ["[{title}]({url}) - {published}".format(**entry) for entry in entries]
    # )
    # rewritten = replace_chunk(rewritten, "blog", entries_md)

    # readme.open("w").write(rewritten)

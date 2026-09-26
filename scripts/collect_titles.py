import argparse
import asyncio
import csv
import os
from dataclasses import dataclass
from html import unescape
from pathlib import Path

import emoji
import httpx
from dotenv import load_dotenv


API_URL = "https://www.googleapis.com/youtube/v3/search"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEARCH_QUERIES = [
    "haber",
    "spor",
    "futbol",
    "oyun",
    "teknoloji",
    "telefon inceleme",
    "yemek tarifi",
    "vlog",
    "belgesel",
    "ekonomi",
    "film",
    "dizi",
    "müzik",
    "gündem",
    "nasıl yapılır",
    "seyahat",
    "eğitim",
    "bilim",
    "otomobil",
    "sağlık",
]
SEARCH_ORDERS = ("relevance", "date", "viewCount")
CSV_FIELDS = ("title", "label")


def clean_title(title: str) -> str:
    title = unescape(title)
    title = emoji.replace_emoji(title, replace="")
    title = title.replace('"', "")
    return " ".join(title.split())


@dataclass
class SearchState:
    query: str
    order: str
    page_token: str | None = None
    exhausted: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Turkish YouTube video titles into a CSV file."
    )
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data") / "youtube_titles.csv",
    )
    return parser.parse_args()


def get_api_key() -> str:
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY was not found in the environment.")

    return api_key


async def fetch_page(
    client: httpx.AsyncClient,
    api_key: str,
    state: SearchState,
) -> list[dict]:
    params = {
        "part": "snippet",
        "q": state.query,
        "type": "video",
        "maxResults": 50,
        "regionCode": "TR",
        "relevanceLanguage": "tr",
        "order": state.order,
        "key": api_key,
    }

    if state.page_token:
        params["pageToken"] = state.page_token

    response = await client.get(API_URL, params=params)
    data = response.json()

    if response.status_code != 200:
        message = data.get("error", {}).get("message", "YouTube API request failed.")
        raise RuntimeError(message)

    state.page_token = data.get("nextPageToken")
    state.exhausted = not state.page_token
    return data.get("items", [])


async def collect_titles(target_count: int, api_key: str) -> list[dict[str, str]]:
    states = [
        SearchState(query=query, order=order)
        for order in SEARCH_ORDERS
        for query in SEARCH_QUERIES
    ]
    titles: list[dict[str, str]] = []
    seen_video_ids: set[str] = set()
    state_index = 0
    request_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        while len(titles) < target_count and request_count < 100:
            state = states[state_index % len(states)]
            state_index += 1

            if state.exhausted:
                if all(item.exhausted for item in states):
                    break
                continue

            items = await fetch_page(client, api_key, state)
            request_count += 1

            for item in items:
                video_id = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})

                if not video_id or video_id in seen_video_ids:
                    continue

                title = clean_title(snippet.get("title", ""))

                if not title:
                    continue

                seen_video_ids.add(video_id)
                titles.append(
                    {
                        "title": title,
                        "label": "",
                    }
                )

                if len(titles) >= target_count:
                    break

    return titles


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


async def main() -> None:
    args = parse_args()

    if args.count <= 0:
        raise ValueError("--count must be greater than zero.")

    api_key = get_api_key()
    titles = await collect_titles(args.count, api_key)
    write_csv(titles, args.output)
    print(f"Collected {len(titles)} unique titles into {args.output}")


if __name__ == "__main__":
    asyncio.run(main())

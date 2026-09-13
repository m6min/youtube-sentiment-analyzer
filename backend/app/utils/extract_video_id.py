from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str | None:
    """Function to extract youtube video id from directly video url
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # if id is in path
    if hostname in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/")
        return video_id if video_id else None

    if hostname in ("www.youtube.com","youtube.com","m.youtube.com"):
        # if id is in query parameters
        if parsed.path == "/watch":
            query_params = parse_qs(parsed.query)
            return query_params.get("v", [None])[0]

        # if id is in path with /embed or shorts
        for prefix in ("/embed","/v/","/shorts/"):
            if parsed.path.startswith(prefix):
                return parsed.path.split(prefix)[1].split("/")[0]

    return None
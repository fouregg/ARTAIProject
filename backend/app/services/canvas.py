"""Deterministic canvas pages with no repeated known subject on a page."""
import math
import re

from app.schemas import DomeItemOut


def subject_key(prompt: str) -> str:
    normalized = " ".join(prompt.lower().split())
    # Only unpack our known batch templates; arbitrary visitors' prompts stay intact.
    if ("an original artwork for a public art exhibition." in normalized or
            "one coherent square artwork, not a collage or a grid." in normalized):
        match = re.match(r"^create .+? (?:of|depicting) (.+?)\. ", normalized)
        if match:
            return match.group(1)
    return normalized


def paginate(items: list[DomeItemOut], page_size: int) -> list[DomeItemOut]:
    groups: dict[str, list[DomeItemOut]] = {}
    for item in items:
        groups.setdefault(subject_key(item.prompt), []).append(item)
    if not groups:
        return []
    # Repeated subjects may require more pages than ordinary slicing into groups of 50.
    page_count = max(math.ceil(len(items) / page_size), max(map(len, groups.values())))
    pages: list[list[DomeItemOut]] = [[] for _ in range(page_count)]
    for group in sorted(groups.values(), key=lambda group: (-len(group), group[0].position, group[0].id)):
        destinations = sorted(range(page_count), key=lambda index: (len(pages[index]), index))
        for item, destination in zip(group, destinations):
            pages[destination].append(item)
    # The last page still contains the newest work and gets the longer display interval.
    pages.sort(key=lambda page: max((item.position, item.id) for item in page))
    result = []
    for page_index, page in enumerate(pages):
        assert len(page) <= page_size
        for item in sorted(page, key=lambda item: (item.position, item.id)):
            result.append(item.model_copy(update={"page_index": page_index}))
    return result

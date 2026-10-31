"""Validate local source snapshots and generate retrieval chunks from reviewed notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"
MANIFEST_PATH = KNOWLEDGE_DIR / "manifest.json"
OUTPUT_PATH = KNOWLEDGE_DIR / "chunks.jsonl"
METADATA_PATTERN = re.compile(r"^- \*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$")


class PageTextExtractor(HTMLParser):
    """Collect visible page text while skipping scripts and styles."""

    def __init__(self) -> None:
        """Prepare the parser's text buffer and skipped-tag counter."""
        super().__init__()
        self.fragments: list[str] = []
        self.skipped_tags = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Ignore embedded content that is not visible page text."""
        if tag in {"script", "style", "noscript"}:
            self.skipped_tags += 1

    def handle_endtag(self, tag: str) -> None:
        """Resume collecting visible text after embedded content closes."""
        if tag in {"script", "style", "noscript"} and self.skipped_tags:
            self.skipped_tags -= 1

    def handle_data(self, data: str) -> None:
        """Keep visible text fragments for source section matching."""
        if not self.skipped_tags and data.strip():
            self.fragments.append(data.strip())

    @staticmethod
    def normalize(fragments: list[str]) -> str:
        """Normalize fragments so markup and whitespace changes do not affect hashes."""
        return " ".join(" ".join(fragments).split())


def read_manifest() -> dict[str, object]:
    """Load and validate the machine-readable source inventory."""
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot read {MANIFEST_PATH}: {error}") from error

    if not isinstance(manifest, dict):
        raise SystemExit("manifest.json must contain a JSON object.")
    if manifest.get("schema_version") != 1 or not manifest.get("sources"):
        raise SystemExit("manifest.json must use schema_version 1 and list sources.")
    return manifest


def format_page_date(value: str) -> str:
    """Format an ISO date without relying on platform-specific strftime flags."""
    parsed_date = date.fromisoformat(value)
    return f"{parsed_date.day} {parsed_date:%B %Y}"


def get_snapshot(source: dict[str, object], download: bool) -> tuple[bytes, Path]:
    """Read the local snapshot, downloading it only when explicitly requested."""
    relative_path = source.get("local_snapshot")
    if not isinstance(relative_path, str):
        raise SystemExit(f"Source {source.get('id')} has no local_snapshot path.")

    snapshot_path = KNOWLEDGE_DIR / relative_path
    if not snapshot_path.is_file():
        if not download:
            raise SystemExit(
                f"Missing local source: {snapshot_path}\n"
                "Run with --download to fetch the reviewed source version."
            )

        url = source.get("url")
        if not isinstance(url, str):
            raise SystemExit(f"Source {source.get('id')} has no download URL.")
        request = Request(url, headers={"User-Agent": "Assessment2KnowledgePrep/1.0"})
        try:
            with urlopen(request, timeout=30) as response:
                source_bytes = response.read()
        except (OSError, URLError) as error:
            raise SystemExit(f"Could not download {url}: {error}") from error
    else:
        source_bytes = snapshot_path.read_bytes()

    return source_bytes, snapshot_path


def verify_snapshot(source: dict[str, object], source_bytes: bytes) -> str:
    """Validate WHO FAQ text and return its normalized-content hash."""
    parser = PageTextExtractor()
    parser.feed(source_bytes.decode("utf-8", errors="replace"))
    page_text = parser.normalize(parser.fragments)

    page_date = source.get("page_date")
    if not isinstance(page_date, str):
        raise SystemExit(f"Source {source.get('id')} has no page_date.")
    expected_date = format_page_date(page_date)
    if expected_date not in page_text:
        raise SystemExit(
            f"The local source {source.get('id')} is missing page date {expected_date}."
        )
    start_marker = "What is diabetes?"
    end_marker = "sometimes listening is more helpful than offering solutions."
    start = page_text.find(start_marker)
    end = page_text.find(end_marker, start)
    if start < 0 or end < 0:
        raise SystemExit(
            f"The local source {source.get('id')} is missing the reviewed FAQ text."
        )
    article_text = page_text[start : end + len(end_marker)]
    required_text = (
        "What are the main types of diabetes?",
        "How is diabetes treated and managed?",
        "psychosocial support",
    )
    missing = [text for text in required_text if text not in article_text]
    if missing:
        raise SystemExit(
            f"The local source {source.get('id')} is missing reviewed content: "
            + ", ".join(missing)
        )

    actual_hash = hashlib.sha256(article_text.encode("utf-8")).hexdigest()
    expected_hash = source.get("content_sha256")
    if actual_hash != expected_hash:
        raise SystemExit(
            f"Source {source.get('id')} has different FAQ content.\n"
            f"Expected content SHA-256: {expected_hash}\n"
            f"Actual content SHA-256:   {actual_hash}\n"
            "Review the updated FAQ and notes before changing the manifest."
        )
    return actual_hash


def parse_note(path: Path) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Read source metadata and one reviewed passage per level-two heading."""
    metadata: dict[str, str] = {}
    sections: list[tuple[str, str]] = []
    section_name: str | None = None
    section_lines: list[str] = []

    def save_section() -> None:
        """Store a non-empty section with its wrapped lines normalized."""
        if section_name is None:
            return
        text = " ".join(" ".join(section_lines).split())
        if text:
            sections.append((section_name, text))

    for line in path.read_text(encoding="utf-8").splitlines():
        metadata_match = METADATA_PATTERN.match(line)
        if metadata_match:
            metadata[metadata_match.group("key")] = metadata_match.group("value")
        elif line.startswith("## "):
            save_section()
            section_name = line[3:].strip()
            section_lines = []
        elif section_name is not None:
            section_lines.append(line)

    save_section()
    if not sections:
        raise SystemExit(f"No content sections found in {path}.")
    return metadata, sections


def build_chunks(manifest: dict[str, object]) -> list[dict[str, str]]:
    """Build stable JSONL records from the notes listed for each source."""
    chunks: list[dict[str, str]] = []
    sources = manifest["sources"]
    assert isinstance(sources, list)

    for source in sources:
        assert isinstance(source, dict)
        source_hash = str(source["content_sha256"])
        note_files = source.get("note_files")
        if not isinstance(note_files, list) or not note_files:
            raise SystemExit(f"Source {source.get('id')} has no note_files.")
        source_chunk_count = 0

        for note_name in note_files:
            if not isinstance(note_name, str):
                raise SystemExit(
                    f"Invalid note filename for source {source.get('id')}."
                )
            note_path = KNOWLEDGE_DIR / note_name
            try:
                metadata, sections = parse_note(note_path)
            except OSError as error:
                raise SystemExit(
                    f"Cannot read curated note {note_path}: {error}"
                ) from error

            expected_metadata = {
                "Source ID": str(source["id"]),
                "Source title": str(source["title"]),
                "Publisher": str(source["publisher"]),
                "Source page": str(source["url"]),
                "Page date": format_page_date(str(source["page_date"])),
            }
            for key, expected in expected_metadata.items():
                if metadata.get(key) != expected:
                    raise SystemExit(
                        f"{note_path.name} has {key}={metadata.get(key)!r}; "
                        f"expected {expected!r}."
                    )

            for section, text in sections:
                source_chunk_count += 1
                chunks.append(
                    {
                        "chunk_id": f"{source['id']}-{source_chunk_count:03d}",
                        "source_id": str(source["id"]),
                        "source_title": str(source["title"]),
                        "source_publisher": str(source["publisher"]),
                        "section": section,
                        "source_url": str(source["url"]),
                        "page_date": str(source["page_date"]),
                        "source_content_sha256": source_hash,
                        "curated_note_file": note_name,
                        "text": text,
                    }
                )
    return chunks


def write_chunks(chunks: list[dict[str, str]]) -> None:
    """Write deterministic UTF-8 JSONL for the local retrieval index."""
    lines = [json.dumps(chunk, ensure_ascii=False) for chunk in chunks]
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Validate source snapshots and regenerate the curated chunk file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download",
        action="store_true",
        help="download a missing snapshot and accept it only if its hash matches",
    )
    args = parser.parse_args()

    manifest = read_manifest()
    sources = manifest["sources"]
    assert isinstance(sources, list)
    for source in sources:
        assert isinstance(source, dict)
        source_bytes, snapshot_path = get_snapshot(source, download=args.download)
        verify_snapshot(source, source_bytes)
        if not snapshot_path.exists():
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_bytes(source_bytes)

    chunks = build_chunks(manifest)
    write_chunks(chunks)
    print(f"Wrote {len(chunks)} chunks to {OUTPUT_PATH.relative_to(PROJECT_ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

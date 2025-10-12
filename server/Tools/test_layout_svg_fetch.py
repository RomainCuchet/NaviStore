import argparse
import os
import sys
import webbrowser
from pathlib import Path

import requests


def fetch_layout_svg(base_url: str, api_key: str, out_file: Path) -> Path:
    url = base_url.rstrip("/") + "/path_optimization/layout_svg"
    headers = {"x-api-key": api_key}

    print(f"Fetching SVG from {url} ...")
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        # Try to surface possible JSON error from FastAPI
        try:
            print("Server error:", resp.json())
        except Exception:
            print("Server error:", resp.text)
        resp.raise_for_status()

    # Log response headers for diagnostics
    print("Status:", resp.status_code)
    print("Content-Type:", resp.headers.get("content-type"))
    print("Content-Encoding:", resp.headers.get("content-encoding"))
    print("Content-Length:", resp.headers.get("content-length"))

    content = resp.content

    # Try decode to strip BOM if present
    text: str
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        # Try with utf-8-sig to strip BOM
        try:
            text = content.decode("utf-8-sig")
        except Exception:
            # Fallback to raw bytes write
            text = ""

    # If decoded to text, ensure it starts with '<' after trimming
    to_write_bytes: bytes
    if text:
        trimmed = text.lstrip("\ufeff\n\r\t ")
        if not trimmed.startswith("<"):
            # Print first 120 chars for debug
            print("First 120 chars of response (trimmed):")
            print(trimmed[:120])
        to_write_bytes = trimmed.encode("utf-8")
    else:
        # Could not decode; write raw but log first 32 bytes
        print("First 32 bytes:", content[:32])
        to_write_bytes = content

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(to_write_bytes)
    size_kb = out_file.stat().st_size / 1024.0
    print(f"Saved SVG to {out_file} ({size_kb:.1f} KB)")
    return out_file


def open_svg(svg_path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(svg_path)  # type: ignore[attr-defined]
        else:
            webbrowser.open(svg_path.as_uri())
        print("Opened SVG in default viewer/browser.")
    except Exception as e:
        print(f"Could not open SVG automatically: {e}")
        print(f"You can open it manually at: {svg_path}")


def test_download_and_open_layout_svg(
    base_url: str,
    api_key: str,
    outfile: Path,
) -> Path:
    svg_path = fetch_layout_svg(base_url, api_key, outfile)
    open_svg(svg_path)
    return svg_path


def main():
    parser = argparse.ArgumentParser(description="Fetch and open current layout SVG.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_URL", "http://localhost:8000"),
        help="API base URL (default from API_URL env or http://localhost:8000)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("API_KEY"),
        required=False,
        help="API key for x-api-key header (default from API_KEY env)",
    )
    parser.add_argument(
        "--out",
        default=str(Path(__file__).parent / "downloaded_layout.svg"),
        help="Output SVG filepath",
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key is required. Set --api-key or API_KEY env var.")
        sys.exit(2)

    out_path = Path(args.out)
    test_download_and_open_layout_svg(args.base_url, args.api_key, out_path)


if __name__ == "__main__":
    main()

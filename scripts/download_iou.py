#!/usr/bin/env python3
"""
Download and normalize recordings listed in tests/IoU/metadata.csv.

Outputs are written to tests/IoU using the filenames in the "Saved As" column.
Every output is mono MP3 audio resampled to 32000 Hz. Rows with Start and End
values are clipped to that interval, in seconds.
"""

import argparse
import csv
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IOU_DIR = PROJECT_ROOT / "tests" / "IoU"
METADATA_PATH = IOU_DIR / "metadata.csv"
TARGET_SR = 32000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=METADATA_PATH,
        help=f"Metadata CSV to read. Default: {METADATA_PATH}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=IOU_DIR,
        help=f"Directory for downloaded files. Default: {IOU_DIR}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing outputs.",
    )
    return parser.parse_args()


def value(row: dict[str, str], name: str) -> str:
    return row.get(name, "").strip()


def parse_offset(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    return float(text)


def download_url(url: str, path: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TemporalLocalizationPaper download_iou.py"},
    )
    with urllib.request.urlopen(request) as response, path.open("wb") as output:
        shutil.copyfileobj(response, output)


def recording_id(row: dict[str, str]) -> str:
    path = urlparse(value(row, "URL")).path.rstrip("/")
    url_id = Path(path).name
    if url_id:
        return url_id.removeprefix("XC")

    recording = value(row, "Recording")
    return recording.removeprefix("XC")


def download_inaturalist(row: dict[str, str], output_dir: Path) -> Path:
    suffix = Path(urlparse(value(row, "URL")).path).suffix or ".download"
    output_path = output_dir / f"{value(row, 'Recording')}{suffix}"
    download_url(value(row, "URL"), output_path)
    return output_path


def download_xenocanto_direct(row: dict[str, str], output_dir: Path) -> Path:
    xc_id = recording_id(row)
    output_path = output_dir / f"XC{xc_id}.mp3"
    download_url(f"https://xeno-canto.org/{xc_id}/download", output_path)
    return output_path


def download_source(row: dict[str, str], temp_dir: Path) -> Path:
    source = value(row, "Source").lower()
    if source == "inaturalist":
        return download_inaturalist(row, temp_dir)
    if source == "xeno-canto":
        return download_xenocanto_direct(row, temp_dir)
    raise ValueError(f"Unsupported source: {value(row, 'Source')}")


def convert_audio(input_path: Path, output_path: Path, start: float | None, end: float | None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        suffix=output_path.suffix,
        delete=False,
        dir=output_path.parent,
    ) as tmp:
        tmp_path = Path(tmp.name)

    command = ["ffmpeg", "-y", "-i", str(input_path)]
    if start is not None and end is not None:
        if end <= start:
            raise ValueError(f"End offset must be greater than Start offset: {start} >= {end}")
        command.extend(["-ss", str(start), "-t", str(end - start)])
    command.extend(
        [
            "-ac",
            "1",
            "-ar",
            str(TARGET_SR),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(tmp_path),
        ]
    )

    try:
        subprocess.run(command, check=True, capture_output=True)
        tmp_path.replace(output_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def process_row(row: dict[str, str], output_dir: Path, force: bool) -> None:
    saved_as = value(row, "Saved As")
    if not saved_as:
        raise ValueError(f"Missing Saved As value for {value(row, 'Recording')}")

    output_path = output_dir / saved_as
    if output_path.exists() and not force:
        print(f"skip      {saved_as}")
        return

    start = parse_offset(value(row, "Start"))
    end = parse_offset(value(row, "End"))
    if (start is None) != (end is None):
        raise ValueError(f"Start and End must both be set or both be empty for {saved_as}")

    print(f"download  {value(row, 'Recording')} -> {saved_as}")
    with tempfile.TemporaryDirectory(prefix="download-iou-") as temp:
        input_path = download_source(row, Path(temp))
        convert_audio(input_path, output_path, start, end)
    print(f"done      {saved_as}")


def main() -> None:
    args = parse_args()
    with args.metadata.open(newline="") as metadata:
        rows = list(csv.DictReader(metadata))

    for row in rows:
        process_row(row, args.output_dir, force=args.force)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Split large JSONL output files into segments under 100MB for GitHub."""

import argparse
import os
from pathlib import Path

MAX_SIZE_MB = 95  # Leave some margin under 100MB


def split_jsonl(input_path: Path, output_dir: Path, max_size_mb: int = MAX_SIZE_MB):
    """Split a JSONL file into segments under max_size_mb."""
    max_bytes = max_size_mb * 1024 * 1024
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = input_path.stem
    segment = 1
    current_size = 0
    current_file = None

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line_bytes = len(line.encode("utf-8"))

            if current_file is None or current_size + line_bytes > max_bytes:
                if current_file:
                    current_file.close()
                    print(f"  {segment_path.name}: {current_size / 1024 / 1024:.1f} MB")

                segment_path = output_dir / f"{base_name}.part{segment:02d}.jsonl"
                current_file = open(segment_path, "w", encoding="utf-8")
                current_size = 0
                segment += 1

            current_file.write(line)
            current_size += line_bytes

    if current_file:
        current_file.close()
        print(f"  {segment_path.name}: {current_size / 1024 / 1024:.1f} MB")

    print(f"\nSplit into {segment - 1} segment(s) in {output_dir}/")


def merge_jsonl(input_dir: Path, output_path: Path):
    """Merge JSONL segments back into a single file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts = sorted(input_dir.glob("*.part*.jsonl"))
    if not parts:
        print(f"No segment files found in {input_dir}")
        return

    with open(output_path, "w", encoding="utf-8") as out:
        for part in parts:
            print(f"  Merging {part.name}...")
            with open(part, "r", encoding="utf-8") as f:
                for line in f:
                    out.write(line)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"\nMerged {len(parts)} segment(s) into {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split/merge JSONL files for GitHub")
    parser.add_argument("action", choices=["split", "merge"], help="Action to perform")
    parser.add_argument(
        "-i",
        "--input",
        default="output/jobs.jsonl",
        help="Input file (split) or directory (merge)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output/segments",
        help="Output directory (split) or file (merge)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=MAX_SIZE_MB,
        help=f"Max segment size in MB (default: {MAX_SIZE_MB})",
    )

    args = parser.parse_args()

    if args.action == "split":
        print(f"Splitting {args.input} into <{args.max_size}MB segments...")
        split_jsonl(Path(args.input), Path(args.output), args.max_size)
    else:
        print(f"Merging segments from {args.input}...")
        merge_jsonl(Path(args.input), Path(args.output))

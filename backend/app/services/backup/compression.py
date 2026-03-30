"""
Compression helpers for backup artifacts.
"""

import gzip
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compress_file(input_path: Path, output_path: Path) -> None:
    with open(input_path, "rb") as file_in, gzip.open(output_path, "wb", compresslevel=6) as file_out:
        while chunk := file_in.read(64 * 1024):
            file_out.write(chunk)

    logger.info("Compressed: %s -> %s", input_path.stat().st_size, output_path.stat().st_size)


def decompress_file(input_path: Path, output_path: Path) -> None:
    with gzip.open(input_path, "rb") as file_in, open(output_path, "wb") as file_out:
        while chunk := file_in.read(64 * 1024):
            file_out.write(chunk)

    logger.info("Decompressed: %s -> %s", input_path.stat().st_size, output_path.stat().st_size)

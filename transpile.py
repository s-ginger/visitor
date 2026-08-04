import io
import tarfile
from pathlib import Path
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
args = parser.parse_args()

INPUT_TAR = Path(args.input)
OUTPUT_TAR = Path(args.output)

TARGET_SIZE = (1024, 576)

with tarfile.open(INPUT_TAR, "r") as src, \
     tarfile.open(OUTPUT_TAR, "w") as dst:

    for member in src.getmembers():
        if not member.isfile():
            continue

        if Path(member.name).suffix.lower() not in {
            ".png", ".jpg", ".jpeg", ".bmp", ".webp"
        }:
            continue

        fileobj = src.extractfile(member)
        if fileobj is None:
            continue

        img = Image.open(fileobj).convert("RGB")

        img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(
            buf,
            format="WEBP",
            quality=70,
            method=6,
        )
        buf.seek(0)

        info = tarfile.TarInfo(
            Path(member.name).with_suffix(".webp").as_posix()
        )
        info.size = len(buf.getbuffer())

        dst.addfile(info, buf)

print("Done!")
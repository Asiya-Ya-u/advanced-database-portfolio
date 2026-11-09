"""Render the practical evidence as images for the LMS submission.

Item 6 of the brief asks the LMS upload to include supporting screenshots
or evidence. These images are captured from the files the scripts produced.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "screenshots"
FONT = Path(r"C:\Windows\Fonts\consola.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\consolab.ttf")


def render(title: str, body: str, dest: Path, max_lines: int = 42) -> None:
    font = ImageFont.truetype(str(FONT), 15)
    bold = ImageFont.truetype(str(FONT_BOLD), 16)
    lines = body.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["", "... full output is in the evidence text file."]
    width = 1100
    line_h = 22
    height = 70 + line_h * (len(lines) + 1)
    image = Image.new("RGB", (width, height), "#f4f1ea")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 46), fill="#1f4e46")
    draw.text((18, 14), title, font=bold, fill="white")
    y = 62
    for line in lines:
        draw.text((18, y), line[:140], font=font, fill="#1c2430")
        y += line_h
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def main() -> None:
    jobs = [
        (
            "Portfolio 2 — query results",
            ROOT / "portfolio-2-query-optimisation" / "evidence" / "query-results.txt",
            OUT / "02-query-results.png",
            36,
        ),
        (
            "Portfolio 2 — plans after indexes",
            ROOT / "portfolio-2-query-optimisation" / "evidence" / "plans-after-indexes.txt",
            OUT / "03-query-plans.png",
            40,
        ),
        (
            "Portfolio 3 — transaction and concurrency log",
            ROOT / "portfolio-3-transactions-concurrency" / "evidence" / "transaction-log.txt",
            OUT / "04-transaction-log.png",
            46,
        ),
        (
            "Portfolio 4 — NoSQL results",
            ROOT / "portfolio-4-nosql" / "evidence" / "nosql-results.txt",
            OUT / "05-nosql-results.png",
            40,
        ),
        (
            "Portfolio 5 — shard and replica log",
            ROOT / "portfolio-5-distributed-cloud" / "evidence" / "cluster-log.txt",
            OUT / "06-cluster-log.png",
            46,
        ),
    ]
    for title, source, dest, limit in jobs:
        render(title, source.read_text(encoding="utf-8"), dest, limit)
        print(dest.name)


if __name__ == "__main__":
    main()

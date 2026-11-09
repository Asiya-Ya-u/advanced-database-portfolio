"""Turn lms-summary.md into the PDF submitted on the LMS.

Requires fpdf2. The body font is Calibri from the Windows font folder so that
the registration apostrophe and the naira amounts render correctly.
"""

from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "lms-summary.md"
OUTPUT = HERE / "lms-summary.pdf"
FONT = Path(r"C:\Windows\Fonts")


def main() -> None:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(18, 16, 18)
    pdf.add_font("Calibri", "", str(FONT / "calibri.ttf"))
    pdf.add_font("Calibri", "B", str(FONT / "calibrib.ttf"))
    pdf.add_font("Calibri", "I", str(FONT / "calibrii.ttf"))
    pdf.add_page()

    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            pdf.ln(1)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Calibri", "B", 16)
            pdf.multi_cell(0, 8, line[2:].replace("**", ""), new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Calibri", "B", 13)
            pdf.multi_cell(0, 7, line[3:].replace("**", ""), new_x="LMARGIN", new_y="NEXT")
        elif line.strip() == "":
            pdf.ln(1.5)
        else:
            bold = line.startswith("**") and "**" in line[2:]
            pdf.set_font("Calibri", "B" if bold else "", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5.6, line.replace("**", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT))
    print(f"Wrote {OUTPUT} ({pdf.pages_count} pages)")


if __name__ == "__main__":
    main()

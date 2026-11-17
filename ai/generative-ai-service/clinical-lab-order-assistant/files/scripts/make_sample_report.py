"""Draw the fictional external lab report used in the demo: uv run python scripts/make_sample_report.py

Output: web/public/samples/al-noor-lab-report.png. The patient, clinic and values are invented.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "web/public/samples/al-noor-lab-report.png"
W, H = 1240, 1500
BLUE, INK, GREY, LINE = (23, 94, 160), (28, 36, 48), (110, 120, 132), (205, 212, 220)

image = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(image)
d.rectangle([0, 0, W, 150], fill=(238, 245, 252))
d.rectangle([60, 40, 110, 110], fill=BLUE)
d.text((75, 55), "+", fill="white", font_size=48)
d.text((135, 44), "Al-Noor Medical Center", fill=BLUE, font_size=40)
d.text((137, 98), "Clinical Laboratory  ·  Riyadh  ·  Accredited", fill=GREY, font_size=22)
d.text((W - 420, 50), "LABORATORY REPORT", fill=INK, font_size=28)
d.text((W - 420, 92), "Report no. ANL-26-091284", fill=GREY, font_size=20)

y = 200
for label, value in [("Patient", "Mohammed Al-Qahtani"), ("Patient ID", "AN-55120"), ("Sex / Age", "Male / 38"),
                     ("Collected", "2026-09-28 08:40"), ("Reported", "2026-09-28 15:10"), ("Referring", "Dr. Al-Otaibi")]:
    d.text((60, y), label, fill=GREY, font_size=20)
    d.text((260, y), value, fill=INK, font_size=22)
    y += 38
d.line([60, y + 10, W - 60, y + 10], fill=LINE, width=2)

y += 50
rows = [
    ("HAEMATOLOGY", None),
    ("Haemoglobin", "15.3", "g/dL", "13.0 – 17.0"),
    ("White cell count", "6.9", "x10^9/L", "4.0 – 11.0"),
    ("Platelets", "244", "x10^9/L", "150 – 400"),
    ("CHEMISTRY", None),
    ("Creatinine", "82", "µmol/L", "62 – 106"),
    ("eGFR", "> 90", "mL/min/1.73m²", "> 60"),
    ("Sodium", "140", "mmol/L", "136 – 145"),
    ("Potassium", "4.1", "mmol/L", "3.5 – 5.1"),
    ("ALT", "28", "U/L", "< 41"),
    ("LIPID PROFILE (fasting)", None),
    ("Total cholesterol", "5.4", "mmol/L", "< 5.2"),
    ("LDL cholesterol", "3.4", "mmol/L", "< 3.4"),
    ("HDL cholesterol", "1.1", "mmol/L", "> 1.0"),
    ("Triglycerides", "1.9", "mmol/L", "< 1.7"),
    ("DIABETES / ENDOCRINE", None),
    ("HbA1c", "5.6", "%", "< 5.7"),
    ("TSH", "1.9", "mIU/L", "0.4 – 4.0"),
    ("VITAMINS", None),
    ("Vitamin D (25-OH)", "64", "nmol/L", "50 – 125"),
]
d.text((60, y), "Test", fill=GREY, font_size=20); d.text((560, y), "Result", fill=GREY, font_size=20)
d.text((740, y), "Unit", fill=GREY, font_size=20); d.text((960, y), "Reference", fill=GREY, font_size=20)
y += 36
d.line([60, y, W - 60, y], fill=LINE, width=2)
y += 14
for row in rows:
    if row[1] is None:
        y += 10
        d.text((60, y), row[0], fill=BLUE, font_size=22)
        y += 40
        continue
    name, result, unit, ref = row
    d.text((60, y), name, fill=INK, font_size=23)
    d.text((560, y), result, fill=INK, font_size=23)
    d.text((740, y), unit, fill=GREY, font_size=21)
    d.text((960, y), ref, fill=GREY, font_size=21)
    y += 40
d.line([60, y + 10, W - 60, y + 10], fill=LINE, width=2)
d.text((60, y + 30), "Validated by: Dr. S. Hamdan, Consultant Chemical Pathologist", fill=GREY, font_size=20)
d.text((60, y + 62), "FICTIONAL DOCUMENT CREATED FOR A SOFTWARE DEMONSTRATION. Not a real patient, clinic or result.", fill=(170, 60, 60), font_size=19)

OUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUT, optimize=True)
print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")

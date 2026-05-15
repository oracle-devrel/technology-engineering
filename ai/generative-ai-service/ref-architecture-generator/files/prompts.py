"""OCI architecture diagram style guide prepended to every image generation prompt."""

OCI_STYLE_GUIDE = """You are generating a professional Oracle Cloud Infrastructure (OCI) reference architecture diagram. Produce a clean flat vector-style technical illustration matching the aesthetic of official diagrams published on docs.oracle.com — NOT photorealistic, NOT 3D, NOT isometric, NOT hand-drawn.

OVERALL AESTHETIC
- White background, crisp vector illustration, enterprise documentation style
- Landscape orientation, horizontal composition
- Minimalist, corporate, print-ready, high contrast
- Every element aligned on a clean grid

COLOR PALETTE (use exactly these)
- Icons and primary text: dark navy #1F3A5F
- Compartment / VCN / Subnet dashed borders and their corner labels: burnt orange #C74634
- Zone panel backgrounds: very light warm gray #F4F5F7
- Numbered flow circles: dark charcoal #4A5568 fill with bold white numerals inside
- Small accent colors permitted only inside icons (teal, purple, red, or orange spots)
- No gradients, no shadows, no glow effects

STRUCTURE
- Top-level zones shown as large adjacent rectangular panels with bold dark-navy titles in the top-left corner of each panel
- Physical diagrams: left panel "On Premises", right panel "OCI Region"; inside OCI Region place an "Availability Domain" container holding three "Fault Domain" sub-panels
- Logical diagrams: vertical swim-lane panels such as "Input", "Integration", "Business Logic", "Backend"
- OCI networking boundaries rendered as DASHED rectangles, nested and labelled in their top-left corner:
  - LZ Compartment (burnt orange dashed border)
  - VCN (burnt orange dashed border, nested inside the compartment)
  - Subnet (burnt orange dashed border, nested inside the VCN)
  - Oracle Services Network (separate dashed region grouping managed OCI services)

ICONS (OCI OFFICIAL ICON SET)
- Line-art monochrome in dark navy, uniform size (~90 px tall), thin-to-medium stroke, rounded corners, subtle interior accent color
- Every icon has a one- or two-line label in small dark-navy sans-serif text placed directly below the icon, centered
- Use the canonical OCI glyph for each component, including:
  - Users (three figures), On-Premises Equipment (server rack)
  - Dynamic Routing Gateway / DRG and Service Gateway (crossed-arrows glyph)
  - OCI Object Storage (cylinder with circle, triangle, hexagon)
  - Oracle Autonomous Database (cylinder with "A+" mark)
  - Oracle Integration (cloud with two curved arrows)
  - OCI Generative AI models (brain outline with circuit traces)
  - OCI Document Understanding (document with analysis overlay)
  - Oracle Digital Assistant (chat speech bubble)
  - Input UI (monitor with gear), Vector Store (cylinder with search glyph)
  - Remote Data Storage (building with database cylinder)

FLOW ARROWS AND NUMBERED STEPS
- Thin dark-navy arrows with solid triangular arrowheads
- Orthogonal routing only: horizontal and vertical segments joined by right angles
- Numbered sequence markers placed along arrow paths: solid dark-charcoal circles (~24 px diameter) containing a bold white numeral (1, 2, 3, ...)
- Numbering follows the order described in the user's flow

TYPOGRAPHY
- Sans-serif face resembling Oracle Sans or Helvetica
- Zone titles: bold, ~16 pt, dark navy
- Icon labels: regular, ~10 pt, dark navy, centered under the icon
- No italics, no decorative or display fonts

STRICT PROHIBITIONS
- No 3D perspective, no isometric projection
- No shadows, gradients, or glow
- No photorealism, no clip art, no cartoon or sketch style
- No decorative backgrounds or illustrations
- No floating icons without a text label

ARCHITECTURE TO DRAW (follow this description exactly; render every component named, honor every zone/boundary mentioned, and number the flow steps as written):
"""
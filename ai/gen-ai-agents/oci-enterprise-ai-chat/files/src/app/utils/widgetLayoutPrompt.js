export const WIDGET_LAYOUT_PROMPT = `## WIDGETS 2.0 — COMPOSABLE LAYOUTS

Wrap **V1 widgets** inside **layout containers** for complex compositions (dashboards, grids, tabs, nested cards).

### FORMAT
\`\`\`
@@widget
<layout>
  <widget ...v1 keys... />
</layout>
@@
\`\`\`

Use Widgets 2.0 for COMPLEX LAYOUTS (grids, tabs, nested cards).
Use Widgets 1.0 (§§...§§) for SINGLE simple widgets.

### LAYOUT TAGS
| Tag | Attrs | Description |
|-----|-------|-------------|
| \`<row>\` | gap, align, wrap, justify | Horizontal flex |
| \`<col>\` | gap, align | Vertical stack |
| \`<grid>\` | cols, gap | CSS grid |
| \`<card>\` | title, bg, shadow, border, padding, dark | Container (dark="true" for dark theme) |
| \`<tabs>\` | — | Tabbed container |
| \`<tab>\` | label | Tab panel (child of tabs) |
| \`<accordion>\` | — | Collapsible sections |
| \`<section>\` | title, open | Section (child of accordion) |

### THE \`<widget>\` TAG
Renders a V1 widget inside a layout. All attributes use V1 shorthand keys. Always self-closing: \`<widget key="value" />\`

**Display keys:**
| Key | Description | Example |
|-----|-------------|---------|
| t | Title / heading | t="Revenue" |
| s | Subtitle | s="Monthly" |
| d | Description / body | d="Details here" |
| n | Large number | n="$1.2M" |
| ic | Icon (lucide name) | ic="sun" |
| p | Progress bar (0-100) | p="75" |
| i | Image URL or keyword | i="https://..." |
| q | Quote text | q="To be or not to be" |
| cd | Code block | cd="console.log('hi')" |
| ls | List (;-separated) | ls="Item 1;Item 2;Item 3" |
| lk | Links | lk="Google>https://google.com" |

**Status card:** \`st="success|error|warning|info"\` + t + d + bt (button) + bt2
**Table:** \`tb="1" h="Col1;Col2" r="Val1;Val2" r2="Val3;Val4"\`
**Timeline:** \`tl="1" ph="Phase1,Date" ph2="Phase2,Date"\`
**Calendar:** \`cal="1" dy="Mon,3" ev="Title,Time,Color" ev2="..."\`
**Checklist:** \`ck="1" done="Done task" todo="Pending" blocked="Blocked"\`
**Chart (line):** \`ch_ln="Title" x="Q1;Q2;Q3" y="Name:10;20;30"\`
**Chart (bar):** \`ch_br="Title" x="Q1;Q2;Q3" y="Name:10;20;30"\`
**Chart (pie):** \`ch_pie="Title" Organic="45" Direct="30" Social="15"\`
**Chart (donut):** \`ch_don="Title" Slice1="40" Slice2="30" n="center" n_s="label"\`
**KPI grid:** \`grid="3" kpi="Value;Label" kpi2="Value;Label" kpi3="Value;Label"\`
**Risk card:** \`risk="high|medium|low" t="Title" d="Description"\`
**Mail:** \`mail="1" subj="Subject" to="recipient" from="sender" body="content"\`
**Poll:** \`poll="Question" d="Description" op="Option1" op2="Option2" op3="Option3"\`

**Style keys:** \`_c\` (color), \`_dark\` (dark theme), \`_center\` (centered), \`_sz\` (s/m/l size)

### CONVENIENCE TAGS
| Tag | Attrs | Description |
|-----|-------|-------------|
| \`<text>\` | text children (markdown) | Markdown text block |
| \`<divider />\` | — | Horizontal line |
| \`<badge />\` | text, color | Inline status badge |
| \`<image />\` | src, alt, height | Image with lightbox |
| \`<drawio>\` | title, height, src | Draw.io diagram viewer (inline XML or URL) |

### FORM TAGS
| Tag | Attrs |
|-----|-------|
| \`<form>\` | — (wraps inputs) |
| \`<input />\` | name, label, placeholder, type, value |
| \`<textarea />\` | name, label, placeholder, rows, maxrows |
| \`<select>\` | name, label, value |
| \`<option>\` | text children |
| \`<checkbox />\` | name, label, checked |
| \`<radio />\` | name, label, options (;-separated) |
| \`<toggle />\` | name, label, checked |
| \`<slider />\` | name, label, min, max, step, value |
| \`<date />\` | name, label, value |
| \`<time />\` | name, label, value |
| \`<rating />\` | name, label, max, value |
| \`<imageupload />\` | name, label, accept, maxsize, placeholder |
| \`<button />\` | label, action, color |

### COLORS
Named: red, green, blue, yellow, orange, purple — or codes: r, g, b, y, o, p, w, k — or hex: #C74634

### EXAMPLES

**Dashboard:**
@@widget
<row gap="16">
  <widget n="$1.2M" t="Revenue" _c="g" />
  <widget n="45K" t="Users" _c="b" />
  <widget n="+12%" t="Growth" _c="o" />
</row>
@@

**Comparison cards:**
@@widget
<grid cols="2" gap="16">
  <card title="Plan A" shadow="true">
    <widget n="$29/mo" t="Price" _c="b" />
    <widget ls="10 users;5GB storage;Email support" />
  </card>
  <card title="Plan B" shadow="true">
    <widget n="$99/mo" t="Price" _c="g" />
    <widget ls="Unlimited users;100GB storage;Priority support" />
  </card>
</grid>
@@

**Tabbed report:**
@@widget
<tabs>
  <tab label="Overview">
    <col gap="12">
      <widget n="$2.5M" t="Total Sales" _c="g" />
      <widget ch_ln="Trend" x="Q1;Q2;Q3;Q4" y="Sales:100;200;150;300" />
    </col>
  </tab>
  <tab label="Details">
    <widget tb="1" h="Quarter;Revenue;Growth" r="Q1;$500K;+10%" r2="Q2;$750K;+50%" />
  </tab>
</tabs>
@@

**Multi-row dashboard (mix different column counts freely):**
@@widget
<row gap="16">
  <card title="Revenue" shadow="true"><widget n="$1.2M" _c="g" /></card>
  <card title="Users" shadow="true"><widget n="45K" _c="b" /></card>
  <card title="Growth" shadow="true"><widget n="+12%" _c="o" /></card>
</row>
<card title="Monthly Trend" shadow="true">
  <widget ch_ln="Revenue" x="Jan;Feb;Mar;Apr" y="Sales:100;150;120;180" />
</card>
<row gap="16">
  <card title="By Region" shadow="true"><widget ch_pie="Regions" US="45" EU="30" APAC="25" /></card>
  <card title="Pipeline" shadow="true"><widget ch_br="Deals" x="Q1;Q2;Q3" y="Won:10;15;20" y2="Lost:3;2;4" _legend="b" /></card>
</row>
@@
Top-level elements stack vertically with automatic spacing. Each row distributes children equally. A card alone takes full width.

**Dark card with stats:**
@@widget
<card title="Server Status" dark="true" shadow="true">
  <row gap="16">
    <widget n="42%" t="CPU" _c="g" />
    <widget n="7.2 GB" t="Memory" _c="b" />
    <widget n="99.9%" t="Uptime" _c="g" />
  </row>
</card>
@@

**Form (simple):**
@@widget
<card title="Contact Form" shadow="true">
  <form>
    <row gap="12">
      <input name="firstName" label="First Name" placeholder="John" />
      <input name="lastName" label="Last Name" placeholder="Doe" />
    </row>
    <input name="email" label="Email" placeholder="john@example.com" type="email" />
    <select name="topic" label="Topic">
      <option>General</option>
      <option>Support</option>
      <option>Sales</option>
    </select>
    <textarea name="message" label="Message" placeholder="Your message..." rows="4" />
    <button label="Send Message" action="contact_submit" />
  </form>
</card>
@@

**Form (complex layout — layouts nest freely inside forms):**
@@widget
<card title="New Employee Onboarding" shadow="true">
  <form>
    <accordion>
      <section title="Personal Info" open="true">
        <row gap="12">
          <input name="firstName" label="First Name" placeholder="Jane" />
          <input name="lastName" label="Last Name" placeholder="Smith" />
        </row>
        <grid cols="2" gap="12">
          <input name="email" label="Email" type="email" />
          <input name="phone" label="Phone" type="tel" />
          <date name="startDate" label="Start Date" />
          <select name="department" label="Department">
            <option>Engineering</option>
            <option>Design</option>
            <option>Marketing</option>
          </select>
        </grid>
      </section>
      <section title="Preferences">
        <row gap="12">
          <toggle name="remote" label="Remote Work" />
          <toggle name="parking" label="Parking Spot" />
        </row>
        <radio name="laptop" label="Laptop" options="MacBook Pro;ThinkPad;Dell XPS" />
        <slider name="monitorSize" label="Monitor Size (inches)" min="24" max="34" step="2" value="27" />
        <textarea name="notes" label="Additional Notes" placeholder="Any special requirements..." rows="3" />
      </section>
    </accordion>
    <button label="Submit Onboarding" action="onboard_submit" color="green" />
  </form>
</card>
@@

**Form with image upload:**
@@widget
<card title="Submit KYC Documents" shadow="true">
  <form>
    <input name="fullName" label="Full Name" placeholder="Jane Smith" />
    <imageupload name="idPhoto" label="ID Card (front)" accept="image/png,image/jpeg" />
    <imageupload name="proofOfAddress" label="Proof of Address" maxsize="10" />
    <button label="Submit" action="kyc_submit" />
  </form>
</card>
@@

**Action items + next steps (checklist + poll):**
@@widget
<card title="Action Items" shadow="true">
  <widget ck="1" todo="Send proposal" todo2="Schedule deep-dive" />
</card>
<card title="What should we prioritize?" shadow="true">
  <widget poll="Which topic first?" op="Budget" op2="Timeline" op3="Architecture" />
</card>
@@

**Project status (status card + timeline + risk):**
@@widget
<widget st="success" t="Deployment Complete" d="All services running" />
<card title="Project Phases" shadow="true">
  <widget tl="1" ph="Discovery,Week 1-2" ph2="Build,Week 3-6" ph3="Launch,Week 7" />
</card>
<row gap="16">
  <widget risk="high" t="Data Migration" d="Needs rollback plan" />
  <widget risk="low" t="Budget" d="Within tolerance" />
</row>
@@

**Analytics (KPI grid + donut chart + calendar):**
@@widget
<row gap="16">
  <widget grid="3" kpi="$200k;Revenue" kpi2="1.2k;Users" kpi3="98%;Uptime" />
</row>
<row gap="16">
  <card title="Traffic Sources" shadow="true">
    <widget ch_don="Sources" Organic="45" Direct="30" Social="25" n="100%" n_s="total" />
  </card>
  <card title="This Week" shadow="true">
    <widget cal="1" dy="Mon,3" ev="Standup,9:00,b" ev2="Demo,14:00,g" dy2="Wed,5" ev3="Review,11:00,p" />
  </card>
</row>
@@

**Email preview + mail:**
@@widget
<widget mail="1" subj="Proposal: AI Pilot" to="team@acme.com" from="you@company.com" body="Attached is the proposal for the Q2 pilot." />
@@

**Draw.io diagram (inline XML from MCP tool output):**
@@widget
<drawio title="Architecture">
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    ...full XML from tool...
  </root>
</mxGraphModel>
</drawio>
@@

**Draw.io diagram (URL to existing diagram):**
@@widget
<drawio title="System Design" src="https://app.diagrams.net/?lightbox=1&...url..." />
@@

**Collapsible sections (accordion + text + badge + divider):**
@@widget
<accordion>
  <section title="Technical Details" open="true">
    <text>Stack: **Node.js** backend, **React** frontend, **PostgreSQL** database.</text>
    <divider />
    <row gap="8">
      <badge text="Production" color="green" />
      <badge text="v2.1.0" color="blue" />
    </row>
  </section>
  <section title="Requirements">
    <widget ls="Valid passport;Proof of address;Recent photo" />
  </section>
</accordion>
@@

### RULES
1. \`<widget />\` is always self-closing — all data goes in attributes
2. Use V1 shorthand keys as attributes: t, n, d, _c, ch_ln, tb, etc.
3. Duplicate keys get numbered: r, r2, r3 for table rows; ev, ev2, ev3 for events
4. Layouts can nest: row inside card, grid inside tab, etc.
5. \`<widget>\` is always a leaf — never nest other tags inside it
6. One @@widget...@@ block per layout — multiple blocks allowed per message
7. When placing multiple related widgets together, wrap them in a \`<card>\` as a parent container to group them visually`;

export default WIDGET_LAYOUT_PROMPT;

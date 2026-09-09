"use client";

import { Box, Typography, Divider, Tabs, Tab } from "@mui/material";
import { Widget, WidgetV2 } from "../components/widgets";
import { parseWidgetV2Complete } from "../utils/widgetV2Parser";
import { useState } from "react";

const Section = ({ title, children }) => (
  <Box sx={{ mb: 6 }}>
    <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: "#333" }}>
      {title}
    </Typography>
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 3, alignItems: "flex-start" }}>
      {children}
    </Box>
  </Box>
);

const WidgetCard = ({ label, props, onSubmit }) => (
  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
    <Widget props={props} isComplete={true} onSubmit={onSubmit} />
    <Typography variant="caption" sx={{ color: "#666", fontFamily: "monospace", fontSize: "0.7rem" }}>
      {label}
    </Typography>
  </Box>
);

const V2Card = ({ label, xml, onSubmit }) => {
  const tree = parseWidgetV2Complete(xml);
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1, width: "100%" }}>
      <WidgetV2 tree={tree} isComplete={true} onSubmit={onSubmit} />
      <Typography variant="caption" sx={{ color: "#666", fontFamily: "monospace", fontSize: "0.7rem", whiteSpace: "pre-wrap" }}>
        {label}
      </Typography>
    </Box>
  );
};

function TabPanel({ value, index, children }) {
  return value === index ? <Box sx={{ pt: 3 }}>{children}</Box> : null;
}

// ─────────────────────────────────────────
// TAB 0: COMPONENTS (V1 widgets)
// ─────────────────────────────────────────
function ComponentsTab({ handleSubmit }) {
  return (
    <>
      {/* STATUS CARDS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Status Cards (st:type)</Typography>

      <Section title="Status types">
        <WidgetCard label="st:success" props={{ st: "success", t: "Payment successful", d: "Your order has been confirmed.", bt: "Continue", bt2: "View order" }} onSubmit={handleSubmit} />
        <WidgetCard label="st:error" props={{ st: "error", t: "Connection failed", d: "Unable to connect to the server.", bt: "Retry", bt2: "Cancel" }} onSubmit={handleSubmit} />
        <WidgetCard label="st:warning" props={{ st: "warning", t: "Low storage", d: "Consider upgrading your plan.", bt: "Upgrade", bt2: "Dismiss" }} onSubmit={handleSubmit} />
        <WidgetCard label="st:info" props={{ st: "info", t: "New features available", d: "Check out the latest updates.", bt: "Learn more" }} onSubmit={handleSubmit} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* ROW FORM LAYOUT */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Row Form Layout (_rows:1)</Typography>

      <Section title="Basic row forms">
        <WidgetCard label="Email compose form" props={{ _rows: "1", t: "New Message", in: "To", in2: "Subject", ta: "Body", bt: "Send", bt2: "Cancel" }} onSubmit={handleSubmit} />
        <WidgetCard label="Contact form with select" props={{ _rows: "1", t: "Contact Us", in: "Name", in2: "Email", sl: "Department?Sales;Support;Technical;Other", ta: "Message", bt: "Submit" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Settings forms">
        <WidgetCard label="Settings with toggles and slider" props={{ _rows: "1", t: "Settings", sl: "Theme?Light;Dark;Auto", tg: "Notifications", tg2: "Sound effects", rg: "Volume?0-100", bt: "Save" }} onSubmit={handleSubmit} />
        <WidgetCard label="Profile form with date picker" props={{ _rows: "1", t: "Profile", s: "Update your information", in: "Username", in2: "Email", sl: "Timezone?UTC;EST;PST;GMT", dt: "Birthday", bt: "Update", bt2: "Cancel" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Order forms">
        <WidgetCard label="Order form" props={{ _rows: "1", t: "Order Parts", in: "Part Number", in2: "Quantity", sl: "Priority?Low;Normal;High;Urgent", ta: "Notes", bt: "Submit Order" }} onSubmit={handleSubmit} />
        <WidgetCard label="Meeting scheduler" props={{ _rows: "1", t: "Schedule Meeting", dt: "Date", tm: "Time", in: "Title", sl: "Duration?30 min;1 hour;2 hours", ta: "Agenda", bt: "Schedule", bt2: "Cancel" }} onSubmit={handleSubmit} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* DEFAULT VALUES */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Default Values (=value)</Typography>

      <Section title="Text inputs with defaults">
        <WidgetCard label="in:Name=John Smith|in:Email=john@example.com" props={{ _rows: "1", t: "Profile", in: "Name=John Smith", in2: "Email=john@example.com", bt: "Submit" }} onSubmit={handleSubmit} />
        <WidgetCard label="ta:Notes=Default text" props={{ _rows: "1", t: "Message", ta: "Notes=This is a pre-filled message\nwith multiple lines", bt: "Submit" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Selects and toggles with defaults">
        <WidgetCard label="sl:Theme?Light;Dark;Auto=Dark" props={{ _rows: "1", t: "Settings", sl: "Theme?Light;Dark;Auto=Dark", sl2: "Language?English;Spanish;French=Spanish", bt: "Apply" }} onSubmit={handleSubmit} />
        <WidgetCard label="tg:Notifications=true|tg:Sound=false" props={{ _rows: "1", t: "Preferences", tg: "Notifications=true", tg2: "Sound=false", tg3: "Dark mode=true", bt: "Save" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Range and date/time with defaults">
        <WidgetCard label="rg:Volume?0-100=75" props={{ _rows: "1", t: "Audio", rg: "Volume?0-100=75", rg2: "Bass?0-100=50", bt: "Apply" }} onSubmit={handleSubmit} />
        <WidgetCard label="dt:Date=2025-01-15|tm:Time=09:00" props={{ _rows: "1", t: "Schedule", dt: "Date=2025-01-15", tm: "Time=09:00", bt: "Confirm" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Complete form with all defaults">
        <WidgetCard label="Complete form with defaults for editing existing data" props={{ _rows: "1", t: "Edit Profile", s: "All fields pre-filled", in: "Username=johndoe", in2: "Email=john@company.com", sl: "Role?Admin;User;Guest=User", tg: "Newsletter=true", dt: "Birthday=1990-05-15", ta: "Bio=Software developer passionate about clean code", bt: "Update", bt2: "Cancel" }} onSubmit={handleSubmit} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* DISPLAY WIDGETS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Display Widgets</Typography>

      <Section title="Basic Text">
        <WidgetCard label="t:title" props={{ t: "Main Title" }} />
        <WidgetCard label="s:subtitle" props={{ s: "Subtitle" }} />
        <WidgetCard label="d:description" props={{ d: "This is a longer description that explains something in detail." }} />
        <WidgetCard label="t + s + d" props={{ t: "Title", s: "Subtitle", d: "Complete widget description" }} />
      </Section>

      <Section title="Numbers & Progress">
        <WidgetCard label="n:1234" props={{ n: "1,234" }} />
        <WidgetCard label="n + s" props={{ n: "1,234", s: "users" }} />
        <WidgetCard label="p:75 (progress)" props={{ p: "75" }} />
        <WidgetCard label="t + p" props={{ t: "Loading", p: "75" }} />
        <WidgetCard label="n + s + p" props={{ n: "85%", s: "completed", p: "85" }} />
      </Section>

      <Section title="Images (i:url)">
        <WidgetCard label="i:url (simple image)" props={{ i: "https://picsum.photos/seed/widget1/1200/800", t: "Sample image" }} />
        <WidgetCard label="i@bg (background image)" props={{ "i@bg": "https://picsum.photos/seed/widget1/1200/800", t: "Card with background", s: "Text over image", _sz: "l" }} />
      </Section>

      <Section title="Icons (ic:name)">
        <WidgetCard label="ic:sun" props={{ ic: "sun", s: "Sunny" }} />
        <WidgetCard label="ic:cloud" props={{ ic: "cloud", s: "Cloudy" }} />
        <WidgetCard label="ic:alert" props={{ ic: "alert", s: "Alert" }} />
        <WidgetCard label="ic:check" props={{ ic: "check", s: "OK" }} />
        <WidgetCard label="ic:info" props={{ ic: "info", s: "Info" }} />
        <WidgetCard label="ic:star" props={{ ic: "star", s: "Favorite" }} />
        <WidgetCard label="ic:heart" props={{ ic: "heart", s: "Like" }} />
        <WidgetCard label="ic:user" props={{ ic: "user", s: "User" }} />
        <WidgetCard label="ic:mail" props={{ ic: "mail", s: "Mail" }} />
        <WidgetCard label="ic:calendar" props={{ ic: "calendar", s: "Date" }} />
        <WidgetCard label="ic:settings" props={{ ic: "settings", s: "Settings" }} />
        <WidgetCard label="ic:download" props={{ ic: "download", s: "Download" }} />
        <WidgetCard label="ic:trash" props={{ ic: "trash", s: "Delete" }} />
      </Section>

      <Section title="Colors (_c:color)">
        <WidgetCard label="_c:r (red)" props={{ t: "Red", ic: "alert", _c: "r" }} />
        <WidgetCard label="_c:g (green)" props={{ t: "Green", ic: "check", _c: "g" }} />
        <WidgetCard label="_c:b (blue)" props={{ t: "Blue", ic: "info", _c: "b" }} />
        <WidgetCard label="_c:y (yellow)" props={{ t: "Yellow", ic: "star", _c: "y" }} />
        <WidgetCard label="_c:o (orange)" props={{ t: "Orange", ic: "alert", _c: "o" }} />
        <WidgetCard label="_c:p (purple)" props={{ t: "Purple", ic: "heart", _c: "p" }} />
      </Section>

      <Section title="Sizes (_sz:size)">
        <WidgetCard label="_sz:xs" props={{ t: "Extra Small", s: "Very small", _sz: "xs" }} />
        <WidgetCard label="_sz:s" props={{ t: "Small", s: "Small", _sz: "s" }} />
        <WidgetCard label="_sz:m" props={{ t: "Medium", s: "Medium (default)", _sz: "m" }} />
        <WidgetCard label="_sz:l" props={{ t: "Large", s: "Large", _sz: "l" }} />
        <WidgetCard label="_sz:xl" props={{ t: "Extra Large", s: "Very large", _sz: "xl" }} />
      </Section>

      <Section title="Dark Theme (_dark:1)">
        <WidgetCard label="_dark:1" props={{ _dark: "1", t: "Dark Card", s: "With dark theme", d: "Text is automatically light" }} />
        <WidgetCard label="_dark + icon" props={{ _dark: "1", ic: "sun", n: "24°C", s: "Madrid" }} />
        <WidgetCard label="_dark + color bg" props={{ _dark: "1", _bg: "b", t: "Blue Dark", d: "Custom background color" }} />
      </Section>

      <Section title="Centered Layout (_center:1)">
        <WidgetCard label="_center:1" props={{ _center: "1", ic: "check", t: "Centered", d: "Icon on top, text centered" }} />
        <WidgetCard label="_center + dark" props={{ _center: "1", _dark: "1", ic: "sun", n: "28°C", s: "Sunny" }} />
      </Section>

      <Section title="Quote & Code">
        <WidgetCard label="q:quote" props={{ q: "Simplicity is the ultimate sophistication.", s: "- Leonardo da Vinci" }} />
        <WidgetCard label="cd:code" props={{ cd: "const x = 42;\nconsole.log(x);" }} />
      </Section>

      <Section title="Lists (ls:item1;item2;item3)">
        <WidgetCard label="ls:list" props={{ t: "Task list", ls: "Review code;Run tests;Deploy" }} />
        <WidgetCard label="ls + ic + _c" props={{ t: "Technologies", ic: "code", ls: "React;Next.js;Node.js;TypeScript", _c: "b" }} />
      </Section>

      <Section title="Links (lk:label>url)">
        <WidgetCard label="lk:links" props={{ t: "Useful resources", lk: "Documentation>https://docs.example.com;API Reference>https://api.example.com;GitHub>https://github.com" }} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* INTERACTIVE WIDGETS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Interactive Widgets</Typography>

      <Section title="Buttons (bt:label)">
        <WidgetCard label="bt:Click me (single)" props={{ bt: "Click me" }} onSubmit={handleSubmit} />
        <WidgetCard label="Multiple buttons" props={{ t: "Continue?", bt: "Yes", "bt@2": "No" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Input (in:placeholder)">
        <WidgetCard label="in:placeholder + bt" props={{ t: "Your name", in: "Type here...", bt: "Submit" }} onSubmit={handleSubmit} />
        <WidgetCard label="Multiple inputs" props={{ t: "Contact", in: "Name", "in@2": "Email", bt: "Submit", _c: "g" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Textarea (ta:placeholder)">
        <WidgetCard label="ta:placeholder" props={{ t: "Feedback", ta: "Write your message...", bt: "Send" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Select (sl:opt1;opt2;opt3)">
        <WidgetCard label="sl:options + bt" props={{ t: "Choose language", sl: "Spanish;English;French", bt: "Confirm" }} onSubmit={handleSubmit} />
        <WidgetCard label="sl with label: sl:Label?opts" props={{ t: "Settings", sl: "Priority?Low;Medium;High", bt: "Apply" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Multi-Select (ms:opt1;opt2;opt3)">
        <WidgetCard label="ms:options" props={{ t: "Select skills", ms: "React;Vue;Angular;Svelte", bt: "Apply" }} onSubmit={handleSubmit} />
        <WidgetCard label="ms with label" props={{ t: "Preferences", ms: "Topics?AI;Cloud;Security;DevOps", bt: "Save" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Radio Buttons (rd:opt1;opt2;opt3)">
        <WidgetCard label="rd:options" props={{ t: "Deployment", rd: "Cloud;On-Premise;Hybrid", bt: "Confirm" }} onSubmit={handleSubmit} />
        <WidgetCard label="rd with label" props={{ t: "Plan", rd: "Plan?Free;Pro;Enterprise", bt: "Select" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Checkbox (cb:label)">
        <WidgetCard label="cb:label (multiple)" props={{ t: "Preferences", cb: "Notifications", "cb@2": "Newsletter", "cb@3": "Dark mode", bt: "Save" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Toggle (tg:label)">
        <WidgetCard label="tg:label" props={{ t: "Settings", tg: "Notifications", tg2: "Dark mode", tg3: "Sound", bt: "Save" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Range (rg:min-max)">
        <WidgetCard label="rg:0-100" props={{ t: "Volume", rg: "0-100", bt: "Apply" }} onSubmit={handleSubmit} />
        <WidgetCard label="rg with label" props={{ t: "Configure", rg: "Brightness?0-100", bt: "Save" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Star Rating (rt:max)">
        <WidgetCard label="rt:5" props={{ t: "Rate this", rt: "5", bt: "Submit" }} onSubmit={handleSubmit} />
        <WidgetCard label="rt with label" props={{ t: "Feedback", rt: "Experience?5", bt: "Send" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Date Picker (dt:label)">
        <WidgetCard label="dt:label" props={{ t: "Select date", dt: "Date", bt: "Confirm" }} onSubmit={handleSubmit} />
      </Section>

      <Section title="Time Picker (tm:label)">
        <WidgetCard label="tm:label" props={{ t: "Select time", tm: "Time", bt: "Confirm" }} onSubmit={handleSubmit} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* CHARTS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Charts</Typography>

      <Section title="Line Chart (ch_ln)">
        <WidgetCard label="ch_ln:Title|x:...|y:..." props={{ ch_ln: "Monthly Sales", x: "Jan;Feb;Mar;Apr;May", y: "100;150;120;180;200" }} />
        <WidgetCard label="Multi-series" props={{ ch_ln: "Comparison", x: "Q1;Q2;Q3;Q4", y: "This Year:100;120;140;160", y2: "Last Year:90;130;150;170", _legend: "b" }} />
      </Section>

      <Section title="Bar Chart (ch_br)">
        <WidgetCard label="ch_br:Title|x:...|y:..." props={{ ch_br: "Revenue by Region", x: "North;South;East;West", y: "120;95;150;80" }} />
        <WidgetCard label="Stacked bars" props={{ ch_br: "Sales by Quarter", x: "Q1;Q2;Q3;Q4", y: "Online:50;60;70;80", y2: "Store:30;40;35;45", _stack: "1", _legend: "b" }} />
      </Section>

      <Section title="Pie Chart (ch_pie)">
        <WidgetCard label="ch_pie:Title|Cat:value" props={{ ch_pie: "Market Share", Apple: "45", Samsung: "30", Others: "25" }} />
      </Section>

      <Section title="Donut Chart (ch_don)">
        <WidgetCard label="ch_don with center value" props={{ ch_don: "Budget Used", Spent: "65", Remaining: "35", n: "65%", n_s: "used" }} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* CALENDAR/AGENDA */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Calendar / Agenda (cal:1)</Typography>

      <Section title="Single day">
        <WidgetCard label="cal:1|dy:Mon,3|ev:Title,Time,Color" props={{ cal: "1", dy: "Mon,3", ev: "Team Standup,9:00,b", ev2: "Project Review,11:30,g", ev3: "Lunch Break,12:30,o" }} />
      </Section>

      <Section title="Multiple days">
        <WidgetCard label="Multiple days with dy:, dy2:, dy3:" props={{ cal: "1", t: "This Week", dy: "Mon,3", ev: "Standup,9:00,b", ev2: "Planning,14:00,g", dy2: "Tue,4", ev3: "Workshop,10:00,p", ev4: "1:1 Meeting,15:00,o", dy3: "Wed,5", ev5: "Sprint Demo,11:00,r" }} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* STRUCTURED DATA */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Structured Data Widgets</Typography>

      <Section title="Mail (mail:1|subj:|to:|body:)">
        <WidgetCard label="mail:1|subj:Subject|to:recipient|body:content" props={{ mail: "1", subj: "Meeting Tomorrow", to: "team@company.com", body: "Hi team,\n\nReminder about our 10am meeting tomorrow.\n\nBest regards" }} />
        <WidgetCard label="With from and cc" props={{ subj: "Project Update", to: "john@example.com", from: "sarah@example.com", cc: "manager@example.com", body: "The project is on track for delivery next week." }} />
      </Section>

      <Section title="Timeline (tl:1|ph:Phase,Date)">
        <WidgetCard label="tl:1|ph:Phase,Date" props={{ tl: "1", ph: "Discovery,Mar 1-15", ph2: "Planning,Mar 15-30", ph3: "Development,Apr 1-30", ph4: "Testing,May 1-15" }} />
        <WidgetCard label="Horizontal: _dir:h" props={{ t: "Release Roadmap", _dir: "h", ph: "Alpha,Jan", ph2: "Beta,Feb", ph3: "RC,Mar", ph4: "Launch,Apr" }} />
      </Section>

      <Section title="Table (tb:1|h:headers|r:row)">
        <WidgetCard label="tb:1|h:Header1;Header2|r:Cell1;Cell2" props={{ tb: "1", h: "Phase;Cost;Duration", r: "Discovery;$15k;2 weeks", r2: "Planning;$10k;1 week", r3: "Development;$50k;6 weeks" }} />
        <WidgetCard label="With title" props={{ t: "Budget Summary", h: "Item;Amount;Status", r: "Development;$30,000;Approved", r2: "Testing;$10,000;Pending", r3: "Total;$40,000;-" }} />
      </Section>

      <Section title="Checklist (ck:1|done:|todo:|blocked:)">
        <WidgetCard label="ck:1|done:Task|todo:Task|blocked:Task" props={{ ck: "1", done: "Setup environment", done2: "Create database schema", todo: "Build API endpoints", blocked: "Deploy to production" }} />
      </Section>

      <Section title="Section / Collapsible (sec:1)">
        <WidgetCard label="sec:1|t:Title|d:Description" props={{ sec: "1", t: "Technical Details", d: "This section covers implementation specifics." }} />
        <WidgetCard label="With list content" props={{ sec: "1", t: "Requirements", ls: "Valid passport;Proof of address;Recent photo" }} />
      </Section>

      <Section title="Risk Cards (risk:high|medium|low)">
        <WidgetCard label="risk:high" props={{ risk: "high", t: "Data Migration", d: "Risk of data loss during transfer." }} />
        <WidgetCard label="risk:medium" props={{ risk: "medium", t: "Timeline Slippage", d: "Dependencies may cause 1-2 week delay." }} />
        <WidgetCard label="risk:low" props={{ risk: "low", t: "Budget Variance", d: "Minor cost increase expected." }} />
      </Section>

      <Section title="KPI Grid (grid:cols|kpi:Value;Label)">
        <WidgetCard label="grid:3|kpi:Value;Label" props={{ grid: "3", kpi: "$200k;Budget", kpi2: "4;Phases", kpi3: "85%;Progress" }} />
        <WidgetCard label="With colors: kpi:Value;Label;color" props={{ cols: "2", kpi: "156;Active Users;g", kpi2: "23;New Today;b", kpi3: "$12.5k;Revenue;p", kpi4: "4.8;Rating;y" }} />
      </Section>

      <Section title="Poll / Choice Selector (poll:Question|op:Option)">
        <WidgetCard label="poll:Question|op:Option1|op:Option2" props={{ poll: "What language do you prefer?", op: "Python", op2: "JavaScript", op3: "Rust", op4: "Go" }} onSubmit={handleSubmit} />
        <WidgetCard label="With description and _id" props={{ poll: "How would you like to proceed?", d: "Choose an option or type your own", op: "Continue with current plan", op2: "Modify the approach", op3: "Start over", _id: "proceed_choice" }} onSubmit={handleSubmit} />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* IMAGE UPLOAD */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Image Upload</Typography>

      <Section title="<imageupload> — drag & drop or click to select">
        <V2Card
          label={'<imageupload label="ID Card (front)" />'}
          xml={`<imageupload name="idFront" label="ID Card (front)" accept="image/png,image/jpeg" />`}
        />
        <V2Card
          label={'<imageupload label="..." maxsize="10" placeholder="..." />'}
          xml={`<imageupload name="proof" label="Proof of address" maxsize="10" placeholder="Drop your utility bill here" />`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* DRAW.IO DIAGRAMS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Draw.io Diagrams</Typography>

      <Section title="<drawio> — interactive diagram viewer">
        <V2Card
          label={'<drawio title="Simple Flowchart">...xml...</drawio>'}
          xml={`<drawio title="Simple Flowchart">
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="Start" style="rounded=1;whiteSpace=wrap;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="160" y="20" width="120" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="Process" style="rounded=0;whiteSpace=wrap;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="160" y="100" width="120" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="Decision" style="rhombus;whiteSpace=wrap;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="140" y="180" width="160" height="80" as="geometry"/>
    </mxCell>
    <mxCell id="5" value="End" style="rounded=1;whiteSpace=wrap;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="160" y="300" width="120" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="6" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="2" target="3" parent="1"/>
    <mxCell id="7" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="3" target="4" parent="1"/>
    <mxCell id="8" value="Yes" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="4" target="5" parent="1"/>
  </root>
</mxGraphModel>
</drawio>`}
        />
        <V2Card
          label={'<drawio src="https://app.diagrams.net/..." />'}
          xml={`<drawio title="OCI Architecture (URL)" src="https://app.diagrams.net/?dark=0&clibs=Uhttps%3A%2F%2Ffrpj5kvxryk1.objectstorage.us-chicago-1.oci.customer-oci.com%2Fp%2Fpeq8PZJIVio5o1vArY0pXxiV_P3EtKVw0WUEwkfHorlRay5Dp59866n1lxSGRvFn%2Fn%2Ffrpj5kvxryk1%2Fb%2Fppt-mcp-bucket%2Fo%2Foci-library.xml#Uhttps%3A%2F%2Ffrpj5kvxryk1.objectstorage.us-chicago-1.oci.customer-oci.com%2Fp%2Fw96JD0_ZuQo9vH5WGLukAVP1_cxNVo0uw65NAVGkwKTlhydTkZqr0f6s8MPcLFbp%2Fn%2Ffrpj5kvxryk1%2Fb%2Fppt-mcp-bucket%2Fo%2Fdiagrams%2F5592d0f9.xml#%7B%22pageId%22%3A%22u7RqDkc7FG084h2jgLRv%22%7D" />`}
        />
      </Section>
    </>
  );
}

// ─────────────────────────────────────────
// TAB 1: LAYOUTS (V2 composable widgets)
// ─────────────────────────────────────────
function LayoutsTab({ handleSubmit }) {
  return (
    <>
      {/* ROW */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Row Layout</Typography>

      <Section title="<row> — Horizontal flex">
        <V2Card
          label={'<row gap="16">\n  <widget n="$1.2M" t="Revenue" _c="g" />\n  <widget n="45K" t="Users" _c="b" />\n  <widget n="+12%" t="Growth" _c="o" />\n</row>'}
          xml={`<row gap="16">
  <widget n="$1.2M" t="Revenue" _c="g" />
  <widget n="45K" t="Users" _c="b" />
  <widget n="+12%" t="Growth" _c="o" />
</row>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* COL */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Column Layout</Typography>

      <Section title="<col> — Vertical stack">
        <V2Card
          label={'<col gap="12">\n  <widget t="Step 1" d="Initialize project" />\n  <widget t="Step 2" d="Install dependencies" />\n  <widget t="Step 3" d="Run dev server" />\n</col>'}
          xml={`<col gap="12">
  <widget t="Step 1" d="Initialize project" />
  <widget t="Step 2" d="Install dependencies" />
  <widget t="Step 3" d="Run dev server" />
</col>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* GRID */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Grid Layout</Typography>

      <Section title='<grid cols="2"> — CSS Grid'>
        <V2Card
          label={'<grid cols="2" gap="16">\n  <card>...</card>\n  <card>...</card>\n</grid>'}
          xml={`<grid cols="2" gap="16">
  <card title="Plan A" shadow="true">
    <widget n="$29/mo" t="Price" _c="b" />
    <widget ls="10 users;5GB storage;Email support" />
  </card>
  <card title="Plan B" shadow="true">
    <widget n="$99/mo" t="Price" _c="g" />
    <widget ls="Unlimited users;100GB storage;Priority support" />
  </card>
</grid>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* CARD */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Card Container</Typography>

      <Section title="<card> — Container with title, shadow, dark">
        <V2Card
          label={'<card title="Server Status" dark="true" shadow="true">\n  <row gap="16">\n    <widget n="42%" t="CPU" _c="g" />\n    ...\n  </row>\n</card>'}
          xml={`<card title="Server Status" dark="true" shadow="true">
  <row gap="16">
    <widget n="42%" t="CPU" _c="g" />
    <widget n="7.2 GB" t="Memory" _c="b" />
    <widget n="99.9%" t="Uptime" _c="g" />
  </row>
</card>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* TABS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Tabs Layout</Typography>

      <Section title="<tabs> + <tab> — Tabbed container">
        <V2Card
          label={'<tabs>\n  <tab label="Overview">...</tab>\n  <tab label="Details">...</tab>\n</tabs>'}
          xml={`<tabs>
  <tab label="Overview">
    <col gap="12">
      <widget n="$2.5M" t="Total Sales" _c="g" />
      <widget ch_ln="Trend" x="Q1;Q2;Q3;Q4" y="Sales:100;200;150;300" />
    </col>
  </tab>
  <tab label="Details">
    <widget tb="1" h="Quarter;Revenue;Growth" r="Q1;$500K;+10%" r2="Q2;$750K;+50%" />
  </tab>
</tabs>`}
          onSubmit={handleSubmit}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* ACCORDION */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Accordion Layout</Typography>

      <Section title="<accordion> + <section> — Collapsible sections">
        <V2Card
          label={'<accordion>\n  <section title="..." open="true">...</section>\n  <section title="...">...</section>\n</accordion>'}
          xml={`<accordion>
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
</accordion>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* CONVENIENCE TAGS */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Convenience Tags</Typography>

      <Section title="<text>, <divider />, <badge />">
        <V2Card
          label={'<text>Markdown</text> + <divider /> + <badge text="..." color="..." />'}
          xml={`<card title="Convenience Tags Demo" shadow="true">
  <text>This is **bold** and *italic* markdown text.</text>
  <divider />
  <row gap="8">
    <badge text="Active" color="green" />
    <badge text="Beta" color="orange" />
    <badge text="v3.0" color="blue" />
  </row>
</card>`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* V2 WIDGET TYPES */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>V1 Widgets Inside V2 Layouts</Typography>

      <Section title="Status + Timeline + Risk">
        <V2Card
          label={'<widget st="success" ... />\n<widget tl="1" ph="..." />\n<widget risk="high" ... />'}
          xml={`<widget st="success" t="Deployment Complete" d="All services running" />
<card title="Project Phases" shadow="true">
  <widget tl="1" ph="Discovery,Week 1-2" ph2="Build,Week 3-6" ph3="Launch,Week 7" />
</card>
<row gap="16">
  <widget risk="high" t="Data Migration" d="Needs rollback plan" />
  <widget risk="low" t="Budget" d="Within tolerance" />
</row>`}
        />
      </Section>

      <Section title="KPI Grid + Donut Chart + Calendar">
        <V2Card
          label={'<widget grid="3" kpi="..." />\n<widget ch_don="..." />\n<widget cal="1" ... />'}
          xml={`<row gap="16">
  <widget grid="3" kpi="$200k;Revenue" kpi2="1.2k;Users" kpi3="98%;Uptime" />
</row>
<row gap="16">
  <card title="Traffic Sources" shadow="true">
    <widget ch_don="Sources" Organic="45" Direct="30" Social="25" n="100%" n_s="total" />
  </card>
  <card title="This Week" shadow="true">
    <widget cal="1" dy="Mon,3" ev="Standup,9:00,b" ev2="Demo,14:00,g" dy2="Wed,5" ev3="Review,11:00,p" />
  </card>
</row>`}
        />
      </Section>

      <Section title="Checklist + Poll (Action Items)">
        <V2Card
          label={'<widget ck="1" todo="..." />\n<widget poll="..." op="..." />'}
          xml={`<card title="Action Items" shadow="true">
  <widget ck="1" todo="Send proposal" todo2="Schedule deep-dive" />
</card>
<card title="What should we prioritize?" shadow="true">
  <widget poll="Which topic first?" op="Budget" op2="Timeline" op3="Architecture" />
</card>`}
          onSubmit={handleSubmit}
        />
      </Section>

      <Section title="Mail Preview">
        <V2Card
          label={'<widget mail="1" subj="..." to="..." body="..." />'}
          xml={`<widget mail="1" subj="Proposal: AI Pilot" to="team@acme.com" from="you@company.com" body="Attached is the proposal for the Q2 pilot." />`}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* FORM */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Form Tags</Typography>

      <Section title="<form> with <input>, <select>, <checkbox>, <radio>, <toggle>, <slider>, <date>, <time>, <rating>, <imageupload>">
        <V2Card
          label={'<form>\n  <input />\n  <select>...</select>\n  <checkbox />\n  <radio />\n  <toggle />\n  <slider />\n  <date />\n  <time />\n  <rating />\n  <imageupload />\n  <button />\n</form>'}
          xml={`<card title="Complete Form" shadow="true">
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
    <checkbox name="terms" label="I agree to the terms" />
    <radio name="plan" label="Plan" options="Free;Pro;Enterprise" />
    <toggle name="notifications" label="Enable notifications" />
    <slider name="budget" label="Budget" min="0" max="1000" step="50" value="500" />
    <date name="startDate" label="Start Date" />
    <time name="meetingTime" label="Meeting Time" />
    <rating name="satisfaction" label="Satisfaction" max="5" />
    <imageupload name="avatar" label="Profile Photo" />
    <button label="Submit" action="form_submit" />
  </form>
</card>`}
          onSubmit={handleSubmit}
        />
      </Section>

      <Divider sx={{ my: 4 }} />

      {/* MULTI-ROW DASHBOARD */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>Complex Dashboard</Typography>

      <Section title="Multi-row layout mixing different column counts">
        <V2Card
          label="Full dashboard: rows of cards + chart + pie + bar"
          xml={`<row gap="16">
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
</row>`}
        />
      </Section>
    </>
  );
}

// ─────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────
export default function SampleWidgetsPage() {
  const [lastSubmit, setLastSubmit] = useState(null);
  const [tab, setTab] = useState(0);

  const handleSubmit = (data, widgetId) => {
    setLastSubmit({ data, widgetId, time: new Date().toLocaleTimeString() });
    console.log("Widget submitted:", { data, widgetId });
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1200, margin: "0 auto", backgroundColor: "#fafafa", minHeight: "100vh" }}>
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
        Widget Showcase
      </Typography>
      <Typography sx={{ mb: 2, color: "#666" }}>
        All available widgets with their variants
      </Typography>

      {lastSubmit && (
        <Box sx={{ mb: 3, p: 2, backgroundColor: "#e8f5e9", borderRadius: 2, border: "1px solid #a5d6a7" }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: "#2e7d32" }}>
            Last submit ({lastSubmit.time}):
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: "monospace", mt: 0.5 }}>
            {JSON.stringify(lastSubmit.data, null, 2)}
          </Typography>
        </Box>
      )}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: "divider", mb: 1 }}>
        <Tab label="Components (V1)" />
        <Tab label="Layouts (V2)" />
      </Tabs>

      <TabPanel value={tab} index={0}>
        <ComponentsTab handleSubmit={handleSubmit} />
      </TabPanel>
      <TabPanel value={tab} index={1}>
        <LayoutsTab handleSubmit={handleSubmit} />
      </TabPanel>
    </Box>
  );
}

"use client";

import { Box, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Widget, WidgetV2 } from "./index";
import { parseWidgetV2Complete } from "../../utils/widgetV2Parser";
import { COLORS, TYPOGRAPHY } from "../../config/widgetTheme";

const INTERVAL = 4000;
const PAUSE_AFTER_INTERACTION = 6000;

const WIDGETS = [
  {
    label: "Image Card",
    props: {
      t: "Giant Panda",
      s: "Wildlife",
      i: "https://media.istockphoto.com/id/523761634/es/foto/linda-oso-panda-en-un-%C3%A1rbol-para-escalar.jpg?s=612x612&w=0&k=20&c=cgj_GIpPS_hLGY43GsWwhWPctbJgONYXwDdyxyq2-Rw=",
      ic: "heart",
    },
  },
  {
    label: "Status Card — Success",
    props: {
      st: "success",
      t: "Payment successful",
      d: "Your order has been confirmed and will be shipped within 24 hours.",
      bt: "Continue",
      bt2: "View order",
    },
  },
  {
    label: "Status Card — Error",
    props: {
      st: "error",
      t: "Connection failed",
      d: "Unable to connect to the server. Please check your internet connection.",
      bt: "Retry",
      bt2: "Cancel",
    },
  },
  {
    label: "Status Card — Warning",
    props: {
      st: "warning",
      t: "Low storage",
      d: "You're running low on storage space. Consider upgrading your plan.",
      bt: "Upgrade",
      bt2: "Dismiss",
    },
  },
  {
    label: "KPI Grid",
    props: {
      grid: "3",
      kpi: "12;Team Size",
      kpi2: "$50k;Monthly Budget",
      kpi3: "85%;Progress",
    },
  },
  {
    label: "KPI Grid — Colored",
    props: {
      t: "Dashboard",
      cols: "2",
      kpi: "156;Active Users;g",
      kpi2: "23;New Today;b",
      kpi3: "$12.5k;Revenue;p",
      kpi4: "4.8;Rating;y",
    },
  },
  {
    label: "Line Chart",
    props: {
      ch_ln: "Monthly Revenue",
      x: "Jan;Feb;Mar;Apr;May;Jun",
      y: "This Year:100;150;120;180;200;165",
      y2: "Last Year:80;110;105;140;160;150",
      _legend: "b",
    },
  },
  {
    label: "Bar Chart — Stacked",
    props: {
      ch_br: "Sales by Quarter",
      x: "Q1;Q2;Q3;Q4",
      y: "Online:50;60;70;80",
      y2: "In-store:30;40;35;45",
      _stack: "1",
      _legend: "b",
    },
  },
  {
    label: "Pie Chart",
    props: {
      ch_pie: "Traffic Sources",
      Organic: "45",
      Direct: "30",
      Social: "15",
      Referral: "10",
      _colors: "g;b;p;o",
    },
  },
  {
    label: "Donut Chart",
    props: {
      ch_don: "Time Distribution",
      Development: "40",
      Meetings: "25",
      Planning: "20",
      Review: "15",
      n: "8h",
      n_s: "today",
      _colors: "b;o;g;p",
    },
  },
  {
    label: "Calendar / Agenda",
    props: {
      cal: "1",
      t: "This Week",
      dy: "Mon,3",
      ev: "Team Standup,9:00,b",
      ev2: "Sprint Planning,14:00,g",
      dy2: "Tue,4",
      ev3: "Design Workshop,10:00,p",
      ev4: "1:1 Meeting,15:00,o",
      dy3: "Wed,5",
      ev5: "Sprint Demo,11:00,r",
    },
  },
  {
    label: "Checklist",
    props: {
      t: "Sprint Tasks",
      ck: "1",
      done: "Setup environment",
      done2: "Create database schema",
      todo: "Build API endpoints",
      todo2: "Write documentation",
      blocked: "Deploy to production",
    },
  },
  {
    label: "Table",
    props: {
      tb: "1",
      t: "Project Budget",
      h: "Phase;Cost;Duration;Status",
      r: "Discovery;$15,000;2 weeks;Complete",
      r2: "Development;$50,000;6 weeks;In Progress",
      r3: "Testing;$10,000;1 week;Pending",
      r4: "Launch;$5,000;3 days;Pending",
    },
  },
  {
    label: "Timeline",
    props: {
      tl: "1",
      t: "Product Roadmap",
      ph: "Discovery,Mar 1-15",
      ph2: "Planning,Mar 15-30",
      ph3: "Development,Apr 1-30",
      ph4: "Beta Launch,May 1-15",
      ph5: "GA Release,Jun 1",
    },
  },
  {
    label: "Mail",
    props: {
      mail: "1",
      subj: "Meeting Tomorrow",
      to: "team@company.com",
      from: "sarah@example.com",
      cc: "manager@example.com",
      body: "Hi team,\n\nJust a reminder about our 10am meeting tomorrow. Please come prepared with your weekly updates.\n\nBest regards",
    },
  },
  {
    label: "Risk Card",
    props: {
      risk: "high",
      t: "Data Migration",
      d: "Risk of data loss during transfer. Need comprehensive rollback plan.",
    },
  },
  {
    label: "Poll",
    props: {
      poll: "What framework do you prefer?",
      d: "Choose your favorite frontend framework",
      op: "React",
      op2: "Vue",
      op3: "Angular",
      op4: "Svelte",
    },
  },
  {
    label: "Contact Form",
    props: {
      _rows: "1",
      t: "New Message",
      in: "To",
      "in@2": "Subject",
      ta: "Body",
      bt: "Send",
      "bt@2": "Cancel",
    },
  },
  {
    label: "Settings Form",
    props: {
      _rows: "1",
      t: "Settings",
      sl: "Theme?Light;Dark;Auto=Dark",
      tg: "Notifications=true",
      tg2: "Sound effects",
      rg: "Volume?0-100=75",
      bt: "Save",
    },
  },
  {
    label: "Weather Card",
    props: {
      t: "Current weather",
      ic: "sun",
      n: "24°C",
      s: "Madrid",
      d: "Clear sky. Feels like 26°C.",
      _c: "y",
      _sz: "l",
    },
  },
  {
    label: "Quote",
    props: {
      q: "The only way to do great work is to love what you do.",
      s: "Steve Jobs",
      ic: "quote",
      _c: "p",
    },
  },
  {
    label: "Dark Theme Card",
    props: {
      _dark: "1",
      _center: "1",
      ic: "sun",
      n: "28°C",
      s: "Sunny",
      d: "Perfect weather today",
    },
  },
  {
    label: "Server Status",
    props: {
      t: "Server status",
      ic: "check",
      n: "99.9%",
      s: "uptime",
      p: "99",
      _c: "g",
    },
  },
];

const V2_WIDGETS = [
  {
    label: "Row",
    version: 2,
    xml: `<row gap="16">
  <text>Element 1</text>
  <text>Element 2</text>
  <text>Element 3</text>
</row>`,
  },
  {
    label: "Col",
    version: 2,
    xml: `<col gap="12">
  <text>Element 1</text>
  <text>Element 2</text>
  <text>Element 3</text>
</col>`,
  },
  {
    label: "Grid",
    version: 2,
    xml: `<grid cols="2" gap="16">
  <text>Element 1</text>
  <text>Element 2</text>
  <text>Element 3</text>
  <text>Element 4</text>
</grid>`,
  },
  {
    label: "Card",
    version: 2,
    xml: `<card title="Card Title" shadow="true">
  <col gap="12">
    <text>Element 1</text>
    <text>Element 2</text>
  </col>
</card>`,
  },
  {
    label: "Tabs",
    version: 2,
    xml: `<tabs>
  <tab label="Tab 1">
    <text>Element 1</text>
  </tab>
  <tab label="Tab 2">
    <text>Element 2</text>
  </tab>
  <tab label="Tab 3">
    <text>Element 3</text>
  </tab>
</tabs>`,
  },
  {
    label: "Accordion",
    version: 2,
    xml: `<accordion>
  <section title="Section 1" open="true">
    <text>Element 1</text>
  </section>
  <section title="Section 2">
    <text>Element 2</text>
  </section>
  <section title="Section 3">
    <text>Element 3</text>
  </section>
</accordion>`,
  },
];

// Pre-parse V2 trees
const V2_PARSED = V2_WIDGETS.map(w => ({
  ...w,
  tree: parseWidgetV2Complete(w.xml),
}));

export { WIDGETS, V2_WIDGETS };

export default function WidgetCarousel({ interval = INTERVAL, height, showDots = true, version = 'both' }) {
  const [index, setIndex] = useState(0);
  const [mounted, setMounted] = useState(false);
  const [paused, setPaused] = useState(false);
  const pauseTimerRef = useRef(null);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = backward

  // Build combined list based on version filter
  const items = useMemo(() => {
    const v1Items = WIDGETS.map(w => ({ ...w, version: 1 }));
    const v2Items = V2_PARSED.map(w => ({ ...w, version: 2 }));
    if (version === 'v1') return v1Items;
    if (version === 'v2') return v2Items;
    const merged = [];
    const max = Math.max(v1Items.length, v2Items.length);
    for (let i = 0; i < max; i++) {
      if (i < v1Items.length) merged.push(v1Items[i]);
      if (i < v2Items.length) merged.push(v2Items[i]);
    }
    return merged;
  }, [version]);

  const pauseAutoPlay = useCallback(() => {
    setPaused(true);
    if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current);
    pauseTimerRef.current = setTimeout(() => setPaused(false), PAUSE_AFTER_INTERACTION);
  }, []);

  const goTo = useCallback((i) => {
    setDirection(i > index ? 1 : -1);
    setIndex(i);
    pauseAutoPlay();
  }, [index, pauseAutoPlay]);

  const goNext = useCallback(() => {
    setDirection(1);
    setIndex(prev => (prev + 1) % items.length);
    pauseAutoPlay();
  }, [items.length, pauseAutoPlay]);

  const goPrev = useCallback(() => {
    setDirection(-1);
    setIndex(prev => (prev - 1 + items.length) % items.length);
    pauseAutoPlay();
  }, [items.length, pauseAutoPlay]);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => { setIndex(0); }, [version]);

  useEffect(() => {
    if (!mounted || items.length === 0 || paused) return;
    const timer = setInterval(() => {
      setDirection(1);
      setIndex(prev => (prev + 1) % items.length);
    }, interval);
    return () => clearInterval(timer);
  }, [mounted, interval, items.length, paused]);

  useEffect(() => {
    return () => { if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current); };
  }, []);

  if (!mounted || items.length === 0) return null;

  const current = items[index % items.length];

  // Group dots into pages of ~20 for large lists
  const DOT_PAGE_SIZE = 20;
  const dotPage = Math.floor(index / DOT_PAGE_SIZE);
  const dotStart = dotPage * DOT_PAGE_SIZE;
  const dotEnd = Math.min(dotStart + DOT_PAGE_SIZE, items.length);

  const arrowSx = {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: 32,
    height: 32,
    borderRadius: "50%",
    backgroundColor: "rgba(0,0,0,0.06)",
    color: COLORS.text.secondary,
    cursor: "pointer",
    flexShrink: 0,
    transition: "all 0.2s ease",
    "&:hover": {
      backgroundColor: "rgba(0,0,0,0.12)",
      color: COLORS.text.primary,
    },
  };

  const FIXED_HEIGHT = height || 420;

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        height: FIXED_HEIGHT,
      }}
    >
      {/* Left arrow — pinned left, vertically centered in content area */}
      <Box
        onClick={goPrev}
        sx={{
          ...arrowSx,
          position: "absolute",
          left: 0,
          top: `calc((${FIXED_HEIGHT}px - 40px) / 2)`,
          zIndex: 2,
        }}
      >
        <ChevronLeft size={18} />
      </Box>

      {/* Right arrow — pinned right, vertically centered in content area */}
      <Box
        onClick={goNext}
        sx={{
          ...arrowSx,
          position: "absolute",
          right: 0,
          top: `calc((${FIXED_HEIGHT}px - 40px) / 2)`,
          zIndex: 2,
        }}
      >
        <ChevronRight size={18} />
      </Box>

      {/* Widget content — fixed height, centered */}
      <Box sx={{
        position: "absolute",
        top: 0,
        left: 40,
        right: 40,
        bottom: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
      }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={`${version}-${index}`}
            initial={{ opacity: 0, x: direction * 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -40 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              width: "100%",
              maxWidth: 560,
            }}
          >
            {current.version === 2 ? (
              <WidgetV2 tree={current.tree} isComplete={true} disabled={true} />
            ) : (
              <Widget props={current.props} isComplete={true} disabled={true} />
            )}
          </motion.div>
        </AnimatePresence>
      </Box>

      {/* Label + dots — pinned to bottom */}
      <Box sx={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 0.5,
      }}>
        <Typography sx={{
          fontSize: "0.95rem",
          fontWeight: 600,
          color: COLORS.text.primary,
          fontFamily: TYPOGRAPHY.fontFamily,
          letterSpacing: "-0.01em",
        }}>
          {current.label}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography sx={{
            fontSize: "0.65rem",
            color: COLORS.text.muted,
            fontFamily: TYPOGRAPHY.fontFamily,
          }}>
            {index + 1}/{items.length}
          </Typography>
        </Box>

        {showDots && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            {dotStart > 0 && (
              <Typography
                onClick={() => goTo(dotStart - 1)}
                sx={{ fontSize: "0.65rem", color: COLORS.text.muted, cursor: "pointer", px: 0.5, "&:hover": { color: COLORS.text.primary } }}
              >
                ...
              </Typography>
            )}
            {items.slice(dotStart, dotEnd).map((_, i) => {
              const realIndex = dotStart + i;
              return (
                <Box
                  key={realIndex}
                  onClick={() => goTo(realIndex)}
                  sx={{
                    width: realIndex === index ? 18 : 6,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: realIndex === index ? COLORS.primary : "rgba(0,0,0,0.12)",
                    cursor: "pointer",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      backgroundColor: realIndex === index ? COLORS.primary : "rgba(0,0,0,0.25)",
                    },
                  }}
                />
              );
            })}
            {dotEnd < items.length && (
              <Typography
                onClick={() => goTo(dotEnd)}
                sx={{ fontSize: "0.65rem", color: COLORS.text.muted, cursor: "pointer", px: 0.5, "&:hover": { color: COLORS.text.primary } }}
              >
                ...
              </Typography>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
}

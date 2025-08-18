"use client";

import AIChat from "./components/AIChat";
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <AIChat />
        {/* <Box position={"absolute"} sx={{ bottom: 22, right: 22 }}>
          <SignatureAnimation duration={0.1} delay={0}>
            AI Specialists Team
          </SignatureAnimation>
        </Box> */}
      </main>
    </div>
  );
}

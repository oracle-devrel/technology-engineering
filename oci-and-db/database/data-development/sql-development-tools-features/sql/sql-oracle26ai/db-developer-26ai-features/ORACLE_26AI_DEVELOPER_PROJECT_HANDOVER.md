# Oracle AI Database 26ai for Database Developers — Project Handover

**Baseline:** v5 project archive, `oracle_database_developer_content_v5.zip` (October 2026)  
**Audience:** Oracle Database developers (SQL and PL/SQL); also useful to application developers, presenters, and technical enablement teams.  
**Purpose of this document:** Explain the presentation concept, the delivered materials, how to run and extend them, and the editorial and technical guardrails for future contributors.

> **Start here:** This is a developer-oriented presentation and hands-on demonstration collection, **not** an exhaustive Oracle feature dictionary or a production reference implementation. Preserve its clear storyline, concise slide notes, focused demonstrations, and selective deeper references.

## 1. The concept and intended audience experience

The central question is **“What changes for the Oracle Database developer?”** The answer is not “learn every new syntax feature.” It is that Oracle AI Database 26ai offers more ways to remove incidental code, express application intent in the schema, expose data in useful shapes, and keep appropriate processing, concurrency, search, and security close to the data.

The audience should leave understanding **why a capability is interesting**, seeing a credible small example, and wanting to explore further. Some features originated in the 23ai family and are discussed in the 26ai context; do not imply every feature first appeared in 26ai.

The presentation follows a recurring **introduction → capability framing → demo → close-out** rhythm. Not every capability is demonstrated: some are presented as architectural awareness or optional extensions. Do not manufacture demonstrations merely to fill a perceived gap.

### Three complementary content layers

| Layer | Primary use | Expected detail |
|---|---|---|
| **PowerPoint** (`pptx/`) | Live audience narrative, visuals, concise speaker notes | Short, spoken, developer-relevant talking points |
| **Storyline Markdown** (`*_story.md`) | Presenter preparation and coaching | Explanations, why it matters, what to notice, scenarios, caveats, follow-up |
| **Additional-information comparisons** (`additional_information/*.md`) | Answer specific “why this instead of that?” questions | Focused technical differences, examples, adoption trade-offs, official references |

**Authority by purpose:** The PowerPoint sets the presentation message and order; storyline Markdown supports the presenter; SQL notebooks demonstrate the actual executable behavior; comparison documents address questions that may arise. If one layer makes a claim about an executed demo, confirm it against the notebook rather than assuming it ran.

## 2. Storylines and their key messages

| Folder | Storyline | Main point / examples |
|---|---|---|
| `01_write_better_sql` | **Write Better SQL** | `QUALIFY`, aggregate `FILTER`, and `GROUP BY` improvements reduce nesting and repeated expressions while retaining business results. |
| `02_model_data_better` | **Model Data Better** | Data Use Case Domains, annotations, and assertions move reusable semantics, discoverable metadata, and eligible cross-row/table rules into the schema. |
| `03_modern_application_data` | **Modern Application Data** | JSON Relational Duality Views expose relational data as hierarchical documents; SQL and GraphQL-style definitions are authoring options; property graphs and SQL/PGQ query connected data. **GraphQL is not SQL/PGQ** and a GraphQL-style view definition is not itself a GraphQL API endpoint. |
| `04_program_the_database` | **Program the Database** | Multilingual Engine (MLE) runs JavaScript modules inside the database and exposes functions through call specifications; PL/SQL and declarative constraints remain appropriate defaults for many tasks. |
| `05_transactions_concurrency` | **Transactions & Concurrency** | Lock-Free Reservations, Sessionless Transactions, Transaction Priorities, Saga support, and Transactional Event Queues address different concurrency, lifetime, distributed-workflow, and event-consistency needs. |
| `06_developer_productivity` | **Developer Productivity** | Repeatable DDL (`IF EXISTS` / `IF NOT EXISTS`), `DBMS_DEVELOPER`, Table DDL Change Notification, and SQL Developer for VS Code / SQLcl reduce surrounding work and improve delivery. |
| `07_ai_and_search` | **AI & Search** | Embeddings, vector similarity, and hybrid search help retrieve by meaning alongside structured SQL; importing an ONNX embedding model for in-database inference is an **optional** architectural path. |
| `08_deep_data_security` | **Deep Data Security** | Database-enforced fine-grained authorization with data roles, grants, and trusted end-user context helps protect data consistently across application access paths. |

**Sequencing principle:** The eight groups are a story, not an arbitrary feature list. Preserve their order unless the presentation narrative is deliberately redesigned. Keep the tools/productivity discussion tied to the real notebooks used during the session.

## 3. Delivered project structure

The ZIP currently has a single enclosing folder named `oracle_database_developer_content_final/`. The structure below is relative to that folder.

```text
oracle_database_developer_content_final/
├── README.md                         # Project overview and content principles
├── 00_setup/
│   ├── README.md                     # Environment and prerequisite instructions
│   ├── admin_setup.sql               # Run as administrator in target PDB
│   └── schema_setup.sql              # Run as demo schema
├── 01_write_better_sql/
│   ├── write_better_sql_story.md
│   ├── write_better_sql_demo.sqlnb
│   ├── write_better_sql_cleanup.sql
│   └── additional_information/
├── 02_model_data_better/             # Same story / demo / cleanup pattern
├── 03_modern_application_data/       # Same pattern
├── 04_program_the_database/          # Same pattern
├── 05_transactions_concurrency/     # Same pattern
├── 06_developer_productivity/        # Same pattern
├── 07_ai_and_search/
│   ├── ai_and_search_story.md
│   ├── ai_and_search_demo.sqlnb
│   ├── ai_and_search_cleanup.sql
│   ├── additional_information/
│   └── in_database_embeddings/       # Optional ONNX/model path; own info, notebook, cleanup
├── 08_deep_data_security/            # Same story / demo / cleanup pattern
├── pptx/
│   └── Oracle_AI_Database_26ai_Developer_v5_3_Explore_More.pptx
├── 26ai_developer_navigator.html     # Offline comparison reference; generated artifact
└── build_navigator.py               # Rebuilds HTML from comparison Markdown
```

The `.sqlnb` files are **SQL Developer notebook files** with a YAML-like `cells:` structure; they are **not JSON/Jupyter `.ipynb` files**. Keep them in their supported notebook format and test them in the SQL Developer extension for VS Code.

The v5 PowerPoint contains **33 slides**, ending with an exploration slide with QR codes for the 26ai New Features documentation and two Oracle LiveLabs. It is stored under `pptx/`, not at the project root.

## 4. How to prepare and deliver a session

1. **Read** the root `README.md`, then `00_setup/README.md`. The latter is authoritative for prerequisites and environment-specific caveats.
2. **Select an Oracle AI Database 26ai environment** (including supported Autonomous AI Database configurations). Confirm required features, privileges, and resource limits; do not assume every optional capability is enabled.
3. **Run `00_setup/admin_setup.sql`** as an administrative user in the target PDB. It prompts for the demo user if not supplied. Review any configurable directory and tablespace values first.
4. **Run `00_setup/schema_setup.sql`** as the demo schema. Review its version, privilege, package, segment, MLE readiness, and optional ONNX checks. Do not enable model loading unless intentionally preparing the optional path.
5. **Read the relevant `*_story.md`** for the intended message, feature mechanics, what to watch in the demo, and suggested close-out.
6. **Open the corresponding `*_demo.sqlnb`** in the SQL Developer extension for VS Code and run the prepared sequence. Confirm outcomes and adapt spoken claims to what actually executes in that environment.
7. **Use the deck for delivery.** Speaker notes are concise; the Markdown and comparison navigator are presenter preparation or question-answering aids, not material to read verbatim.
8. **Run the matching `*_cleanup.sql`** after the demo or when resetting the environment, following its instructions. Do not casually drop shared or non-demo objects.

**Special cases:** Table DDL Change Notification requires an OCI client and configuration; it is not a standard SQL-only notebook demo. Identity-aware Deep Data Security enforcement requires suitable authenticated end-user context. Saga and TxEventQ may be discussed conceptually rather than demonstrated as full distributed applications. The ONNX embedding path requires a compatible model, access to its location, privileges, and sufficient resources.

### Useful exploration links (also represented by the closing slide)

- [Oracle AI Database 26ai — New Features](https://docs.oracle.com/en/database/oracle/oracle-database/26/nfcoa/)
- [New Features — The Essentials LiveLab](https://livelabs.oracle.com/ords/r/dbpm/livelabs/view-workshop?wid=4213)
- [New Features LiveLab](https://livelabs.oracle.com/ords/r/dbpm/livelabs/view-workshop?wid=3950)

## 5. Maintaining the PowerPoint

**Presentation goal:** Spark interest, demonstrate the key idea, and give developers a reason to investigate their own use cases. Do not turn slide notes into tutorials or a catalog of feature restrictions.

- Keep the **intro → demo → close-out** narrative. Introductions establish the problem; demos show behavior; close-outs reinforce value and likely application consumers. Avoid repeating the same paragraph three times.
- Use concise, natural spoken language. Prefer concrete scenarios (e.g., a metadata cache reacting to DDL; an order event committed with business data) to broad claims of “powerful” features.
- Avoid “not part of this notebook,” “this lab doesn't cover,” and other distracting disclaimers in spoken notes unless omitting a limitation would mislead. Acknowledge what was shown and where it could be useful.
- Preserve the distinction between **demonstrated behavior** and **architectural possibilities**. Never imply a Kafka consumer, GraphQL API, external DDL listener, or identity integration was executed unless it actually was.
- Keep source tags and bibliographies **out of spoken notes**. Maintain source verification separately in working/research materials where needed.
- Keep visual design, storyline order, and terminology consistent. Prefer complete feature names on first mention, then abbreviations (`Transactional Event Queues (TxEventQ)`, `Virtual Private Database (VPD)`).
- Set all new and edited PowerPoint text **proofing language to English (United States), `en-US`**, including notes. Check text runs and masters/layouts; changing the UI language alone is insufficient.
- Use PowerPoint slide-number fields/master or layout mechanisms where practical; do not introduce new manually hard-coded numbers. The deck has undergone footer/numbering work, so verify numbering after reordering slides.
- After edits, render the deck and inspect the affected slides, presenter notes, QR readability, and the complete sequence. Check that the closing QR destinations still work.

### Current closing-slide destinations

The last slide points to the 26ai New Features page and the two LiveLabs listed above. Keep three distinct, scannable QR codes, clear labels, sufficient white space, and visible human-readable link labels where practical. If links change, update the QR payloads **and** labels together and test with a phone.

## 6. Maintaining the storyline Markdown

Each storyline's `*_story.md` is a **presenter coaching document**, not an encyclopedia. The current files use a recognizable structure:

- **Presenter purpose** — the intended audience outcome.
- **Introduction — why developers should care** — developer problem and relevance.
- **Capabilities and what to notice** (or **How it works**) — mechanics and distinctions needed to explain the story.
- **Demo coaching** — what to observe, verify, and emphasize; grounded in the actual notebook.
- **Close-out — the memorable point** — why it matters and where it could apply.
- **Presenter follow-up / Where this could matter**, where useful — plausible application scenarios and likely questions.

When updating a story, **start with the approved slide narrative**, then check the demo notebook, then expand only enough for the presenter to understand and explain it confidently. Preserve useful technical nuances, such as transaction commit boundaries, ordering guarantees, update permissions, and authentication requirements, but avoid recreating the entire Oracle manual.

The Markdown may contain technical references for presenter research; the restriction against source tags primarily concerns **spoken PowerPoint notes**. Keep authoritative references current and avoid unsupported performance claims.

## 7. Additional-information comparisons: purpose and rules

The comparison catalog exists for a specific question: **“Oracle already has an older or familiar approach. Why should a developer learn or adopt this one?”** These files are **optional deep dives**, not mandatory stops in the presentation and not a comprehensive dictionary of Oracle Database features.

**Location:** `NN_storyline/additional_information/<new_feature>_vs_<existing_approach>.md`.

**One comparison per file.** Use the following five-question track:

1. **What is the new capability?**
2. **How did we solve this before?**
3. **What is different?**
4. **What are the advantages and limitations?**
5. **When should developers adopt it?**

Follow with a **Key Takeaway** and **Documentation**. Include a concise practical SQL example or clearly labeled conceptual/runtime scenario; make it substantial enough to support understanding without inventing a full application. For concurrency features, explain **what the database enforces, when it enforces it, and what competing sessions/clients observe**. For scalability claims, distinguish documented architecture from workload-specific benchmark evidence.

Use **Oracle AI Database 26ai official documentation**, ideally one authoritative link per compared feature (SQL Language Reference, PL/SQL packages, or the relevant specialist guide). Use full feature names in titles and filenames when possible; explain acronyms on first mention. Avoid making unrelated features sound like direct replacements.

### Comparisons present in the v5 archive

| Storyline | Files / subjects |
|---|---|
| 01 | SQL BOOLEAN vs. NUMBER/CHAR |
| 02 | Domains vs. CHECK constraints; Domains vs. User-Defined Types |
| 03 | JSON Duality vs. handwritten REST/JSON mapping; native JSON vs. CLOB |
| 04 | SQL Macros vs. PL/SQL functions; MLE JavaScript vs. PL/SQL functions/procedures |
| 05 | Lock-Free Reservations vs. row locking; Lock-Free Reservations vs. JSON Duality optimistic concurrency control; TxEventQ vs. AQ |
| 06 | No comparison file in the supplied baseline |
| 07 | AI Vector Search vs. Oracle Text; Select AI vs. dynamic SQL |
| 08 | Deep Data Security vs. Virtual Private Database (two filename variants; see maintenance note below) |

**Baseline hygiene note:** The archive includes both `deep_data_security_vs_virtual_private_database.md` and `deep_data_security_vs_vpd.md`. They cover the same pairing. **Do not delete either blindly**; review the contents and decide which is canonical before cleaning up, then rebuild the navigator. This is an observation, not a change made by this handover.

**Do not modify comparison files automatically** as a side effect of slide/storyline edits. Propose new comparisons only when real developer questions justify them; avoid catalog sprawl.

## 8. Offline HTML Developer Knowledge Navigator

**File:** `26ai_developer_navigator.html` in the project root. It is a **generated, standalone HTML snapshot**, not the source of truth.

- Double-click it to open with `file://` in a normal browser. No web server or internet connection is required for search, navigation, and embedded content.
- It contains its own HTML, CSS, JavaScript, comparison content, and search index. Documentation hyperlinks naturally require network access.
- Browse by storyline, search comparison text and synonyms, and switch between **Overview** and **Details**. Overview gives the question/takeaway/adoption guidance; Details shows the full comparison and code snippets.
- The navigator does **not** automatically read newly added local Markdown files when opened in the browser. Rebuild it after adding, removing, renaming, or editing comparisons.

**Rebuild from the project root (or any working directory):**

```bash
python3 build_navigator.py
```

The generator uses its own location to find the project root. It discovers folders matching the `NN_name` pattern and `.md` files directly within their `additional_information/` folders; it does not require a hard-coded comparison list. It uses **Python 3.9+ standard library only** and writes `26ai_developer_navigator.html`. It does not modify the source Markdown.

**Important:** It indexes comparison Markdown, **not** the `*_story.md` documents, notebooks, PowerPoint, or nested arbitrary folders. To add a comparison, place it directly under the relevant `additional_information/` folder and rebuild. Verify that the generated comparison count and storyline label are correct. The display label **“Transactions & Concurrency”** is specially handled in the current generator.

If changing the HTML layout, labels, or behavior, **edit `build_navigator.py` and regenerate**. Editing the generated HTML alone will be overwritten at the next build. Keep the navigator simple: it is a quick reference page, not a full reference application. Do not introduce hosting, runtime database dependencies, or external libraries without an explicit design decision.

## 9. Technical accuracy and demo guardrails

- **Oracle documentation:** Verify release-specific syntax and behavior against the **26ai** documentation before changing claims or examples. Record original feature introduction separately if relevant.
- **Runnable vs. conceptual:** Mark examples accurately. A conceptual event-stream diagram or API sequence is not proof of a tested integration.
- **Transactions:** Distinguish Lock-Free Reservations from row locks and from JSON Duality ETAG-based optimistic concurrency; describe timing and outcomes, not just feature names. TxEventQ and AQ both offer transactional messaging; do not claim TxEventQ always outperforms AQ.
- **Modern data:** GraphQL-style syntax can define Duality Views; **SQL/PGQ** is for property-graph pattern queries. GraphQL syntax in a view definition does not itself expose a general GraphQL API. Document updates remain governed by view annotations, constraints, and transactions.
- **MLE:** JavaScript in Oracle is an option alongside PL/SQL, not a universal replacement; external packages and runtime settings require deliberate deployment and testing.
- **AI:** Vector retrieval needs compatible embeddings; in-database ONNX inference is optional and has model/resource prerequisites. Do not conflate retrieval with LLM-generated answers.
- **Security:** Data-role/grant setup is not the same as proving enforcement for multiple authenticated end users. Verify trusted identity context before making end-to-end claims.
- **Resources and privileges:** The setup README discusses Autonomous Always Free storage, ONNX directories, MLE readiness, and OCI client requirements. Respect these constraints; never embed credentials in shared scripts.

## 10. Suggested change workflow for the team

1. **State the intended change:** Which storyline, capability, audience question, or demo behavior is changing? Is it a slide edit, storyline explanation, notebook change, or new comparison?
2. **Inspect related sources:** Read the current slide and notes, storyline Markdown, notebook, cleanup, and any existing comparison before editing. Do not rewrite from memory.
3. **Check the feature claim:** Use current Oracle AI Database 26ai documentation for behavior, availability, syntax, and restrictions.
4. **Update the appropriate layer first:** For narrative changes, finalize slides then align storyline Markdown. For executable behavior, validate the notebook and setup/cleanup before describing it as demonstrated. For a new comparison, add one standalone Markdown file.
5. **Preserve boundaries:** Do not alter unrelated demos, setup, comparison files, or slide visuals merely because they are nearby.
6. **Rebuild the navigator** if comparison Markdown or the generator changed. Do not rebuild it for slide-only or story-only edits unless you intentionally change its scope.
7. **Validate:** Open the deck, check slide ordering/notes/QR codes and `en-US` proofing; run affected notebook cells in a suitable 26ai environment; check cleanup; open the offline navigator and verify counts/search/Overview/Details.
8. **Package and document:** Use a clear version, e.g. `v5.1` for a focused patch; include a short changelog with affected files and known untested items. Preserve the project-relative folder structure in ZIPs.

### Minimum acceptance checklist

- [ ] Storyline and message remain consistent with the deck.
- [ ] Speaker notes are concise, natural, and free of distracting source tags or notebook disclaimers.
- [ ] Any new claim of observed behavior matches a tested demo or is explicitly conceptual.
- [ ] SQL and documentation target the relevant Oracle 26ai capabilities.
- [ ] New/edited slide text and notes use **English (United States)** proofing.
- [ ] Demos and cleanup still operate safely; environment-specific prerequisites are documented.
- [ ] New comparisons follow the five questions and include a coaching example and adoption decision.
- [ ] Navigator regenerated and checked after comparison changes.
- [ ] Existing unrelated content preserved; changed files listed in release notes.

## 11. Ownership and extension principles

The team can extend the collection with additional 26ai capabilities, new practical examples, or more targeted comparisons. Keep each addition tied to a **developer problem and a clear reason to care**. Resist turning the session into a feature inventory, and resist turning the comparison navigator into a general documentation portal. New demos should be small, reproducible, and supported by cleanup; new presenter notes should improve understanding without increasing live narration unnecessarily.

**Recommended next step for maintainers:** Review this handover alongside the v5 archive, run the setup in a disposable 26ai environment, and rehearse the slide-to-notebook transitions. 
---

*This handover documents the supplied v5 archive as inspected. It does not assert that every notebook has been executed or that every external URL has been checked live during handover preparation.*

# Lock-Free Reservations vs. Optimistic Concurrency Control (JSON Relational Duality Views)

> **Developer question:** Both are described as lock-free concurrency features. If two users update the same inventory item, what does Oracle actually enforce, and when would I choose each?

## 1. What is the new capability?

**Lock-Free Reservations (LFR)** let transactions reserve supported **numeric increments or decrements** on a hot row without holding the usual row lock during the reservation. Oracle records pending deltas in a reservation journal, considers other reservations when enforcing the declared `CHECK` constraint, and applies the delta at commit (when it briefly locks the row).

**JSON Relational Duality Views** expose ordinary relational rows as updatable JSON documents. Their **Optimistic Concurrency Control (OCC)** uses a content-based ETAG (`_metadata.etag`) to reject a *stale full-document replacement*. A duality view is a document interface over tables, not a separate JSON copy of the data.

**The distinction:** LFR answers **“Can I reserve this quantity safely?”**; OCC answers **“Has the document I edited changed since I read it?”** Both are database-enforced, but solve different problems.

## 2. How did we solve this before?

- **Hot inventory:** `UPDATE inventory SET available = available - 1 WHERE ...` ordinarily obtains a row lock; other writers to that row can wait. An atomic conditional update (`... WHERE available >= 1`) already prevents negative stock, but does not eliminate row-lock contention.
- **Document editing:** an application might hold a lock during a read/edit/write cycle (undesirable for web or mobile clients), or implement its own version-number check (`UPDATE ... WHERE version = :old_version`). Duality views provide content-based checks across the relational data represented by the document.

## 3. What is different? Practical two-client walkthrough

### A. Lock-Free Reservations: two buyers, three units available

**Setup (SQL; run once):**

```sql
CREATE TABLE demo_inventory_lfr (
  product_id NUMBER PRIMARY KEY,
  available  NUMBER RESERVABLE
             CONSTRAINT demo_stock_nonnegative CHECK (available >= 0)
);
INSERT INTO demo_inventory_lfr VALUES (101, 3);
COMMIT;
```

**Session A (leave uncommitted):**

```sql
UPDATE demo_inventory_lfr
   SET available = available - 2
 WHERE product_id = 101;
-- A reserves two units. Do not commit yet.
```

**Session B, while A is still open:**

```sql
UPDATE demo_inventory_lfr
   SET available = available - 1
 WHERE product_id = 101;
-- B can reserve one more unit without waiting for A's row lock.
COMMIT;
```

**Session A:** `COMMIT;` Final available quantity is **0**. If B had tried `available = available - 2`, the combined reservations would exceed available stock and Oracle would reject the invalid reservation through the constraint. The exact time of the failure and concurrency behavior should be observed in a two-session demo; application code must handle errors and rollback appropriately.

**Where enforcement happens:** Oracle recognizes the `column = column +/- expression` update on the `RESERVABLE` column, records a reservation, validates constraints against outstanding reservations, and applies committed deltas. **It is not a generic lock-free update mechanism**: direct assignment (`SET available = 0`) is not allowed for a reservable update; the update must follow the supported syntax and identify the row by its primary key. Do not combine updates to reservable and ordinary columns in one statement.

**Coaching prompt:** “If 100 shoppers each subtract one unit, should the database force them to wait for a long-held row lock just to express their intended delta?”

### B. JSON Relational Duality View: two editors, one product document

**Conceptual setup:** Suppose an updatable duality view `product_dv` maps a relational `products` table (`product_id`, `name`, `description`, `price`) into a document. The view definition must grant the relevant fields `UPDATE` permission. The following **sample response is illustrative**, not an ETAG value to hardcode:

```json
{
  "_id": 101,
  "name": "Trail Backpack",
  "description": "20-litre pack",
  "price": 89,
  "_metadata": {
    "etag": "E1_EXAMPLE_HASH",
    "asof": "EXAMPLE_SCN"
  }
}
```

An ORDS-enabled duality-view endpoint can expose the document. **Endpoint, credentials, and view creation are prerequisites**; adapt the URL to your configured ORDS schema and view. The API sequence below illustrates an ORDS document replacement, not an executable deployment script.

**1 — Both clients read the same document:**

```http
GET /ords/demo/product_dv/101 HTTP/1.1
Accept: application/json
```

Client A and Client B each receive the document with ETAG **E1** (real ETAGs are Oracle-generated hashes).

**2 — Client A changes price and submits a complete replacement:**

```http
PUT /ords/demo/product_dv/101 HTTP/1.1
Content-Type: application/json
If-Match: "E1_EXAMPLE_HASH"

{
  "_id": 101,
  "name": "Trail Backpack",
  "description": "20-litre pack",
  "price": 95,
  "_metadata": {"etag": "E1_EXAMPLE_HASH"}
}
```

With the correct current ETAG and an updatable view, A's update succeeds; the database's current document now has **E2**. (The example uses placeholder values: substitute the actual GET response's ETAG and the exact payload required by your ORDS endpoint.)

**3 — Client B changes description but sends its stale E1:**

```http
PUT /ords/demo/product_dv/101 HTTP/1.1
Content-Type: application/json
If-Match: "E1_EXAMPLE_HASH"

{
  "_id": 101,
  "name": "Trail Backpack",
  "description": "Recycled-fabric 20-litre pack",
  "price": 89,
  "_metadata": {"etag": "E1_EXAMPLE_HASH"}
}
```

**Expected outcome:** An HTTP endpoint that implements conditional replacement can return **HTTP 412 Precondition Failed** for a stale `If-Match`; the equivalent stale full-document update through SQL raises **ORA-42699**. B must **GET again**, reconcile its intended description edit with A's new price, and retry using E2. Oracle does not silently merge competing complete replacements.

**Where enforcement happens:** the database computes the ETAG from the underlying table columns included in the duality view's ETAG check, compares the submitted version to the current persisted content, and rejects stale writes. This protects against changes made through other duality views or directly against those underlying relational columns, when those changes affect the checked content.

**Important nuance:** The `If-Match` header is an HTTP-layer convention; verify your configured ORDS handler passes/enforces the precondition rather than assuming any arbitrary ORDS route does so. `CHECK`/`NOCHECK` annotations in a duality-view definition control which fields participate in the ETAG; these are **not SQL `CHECK` constraints**. A **partial-document update** using `JSON_TRANSFORM` does **not** automatically compare a supplied document ETAG, so do not claim that every update through a duality view is ETAG-protected. For an ETAG demonstration, use a **full-document replacement** with the original ETAG (or the supported ORDS `If-Match` flow).

**Coaching prompt:** “If an editor has a document open for ten minutes, should the database let them overwrite changes made five minutes ago by someone else?”

### Side-by-side runtime enforcement

| Event | Lock-Free Reservations | Duality-view OCC |
|---|---|---|
| What the client submits | `available = available - 2` | Full JSON replacement + previously read ETAG |
| What Oracle tracks | Pending numeric deltas | Hash of checked document content |
| Conflict rule | Combined reservations must respect constraints | Current document content must match read version |
| Typical successful concurrency | Both valid stock decrements can commit | Nonconflicting reads; writes succeed if ETAG still current |
| Failure the app handles | Constraint/reservation failure; rollback or reject order | Stale-write error / HTTP 412; re-read, reconcile, retry |
| Does it protect the other feature's concern? | **No** document-version check | **No** reservation of limited stock |

## 4. What are the advantages and limitations?

**LFR advantage:** better throughput potential for highly contended, bounded counters or balances. **Limitations:** numeric delta-only updates, specific DML syntax and table/constraint restrictions; measure benefit under realistic contention. It is not a substitute for broader transaction design.

**Duality-view OCC advantage:** natural for web/mobile read-edit-write flows, with content-based conflict detection over relational data and no lock held during user think time. **Limitations:** clients need retry/merge UX; contention can cause repeated failures; ETAG scope depends on `CHECK`/`NOCHECK`; a partial update does not automatically perform the same ETAG check. The document view must be defined with the required update permissions.

**Could both be used in one application?** Yes, for *different operations*: use LFR for a high-contention inventory reservation and a duality view for a product editor's descriptive document. **Do not assume an unrestricted document replacement can directly update a `RESERVABLE` quantity column**: LFR's permitted delta-update rules still apply. Keep the stock-reservation operation behind SQL/PLSQL or a purpose-built API, while using the duality view for document-oriented fields.

## 5. When should developers adopt it?

- Choose **LFR** when many concurrent transactions add/subtract from the *same constrained numeric resource* and conventional row-lock contention is measurable.
- Choose **duality-view OCC** when an application fetches a document, lets a user edit it, then submits a replacement and must avoid lost updates.
- Keep ordinary SQL with conditional updates for simple, low-contention counters; use existing version checks where a duality-view document API would add unnecessary complexity.
- For a commerce application, **combine them at the architecture level**: inventory reservation endpoint for `available - n`; product document endpoint for name/description/price with ETAG checking.

## Key takeaway / 30-second speaker answer

**Both avoid holding locks during long application workflows, but they are not competing implementations of the same guarantee.** Lock-Free Reservations enforce *safe arithmetic on a shared resource*; duality-view Optimistic Concurrency Control prevents *stale document overwrites*. Show two buyers succeeding with three units, then two editors where the second gets HTTP 412. That is the difference developers will remember.

## Documentation — Oracle AI Database 26ai

- [Using Lock-Free Reservation — Application Development Features](https://docs.oracle.com/en/database/oracle/oracle-database/26/adfns/using-lock-free-reservation.html)
- [Using Optimistic Concurrency Control With Duality Views — JSON-Relational Duality Developer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/26/jsnvu/using-optimistic-concurrency-control-duality-views.html)

*Validation note: SQL reservation syntax and documented OCC failure modes were checked against Oracle 26ai documentation. The ORDS example is a coached request/response illustration, not a tested endpoint. Replace illustrative ETAGs and adapt payload/URL to the configured duality view before live execution.*

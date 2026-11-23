# Lock-Free Reservations vs. Conventional Row Locking

> **Developer question:** We already use atomic `UPDATE` and `SELECT FOR UPDATE`. Why would Lock-Free Reservations be worth adopting?

## 1. What is the new capability?

**Lock-Free Reservations (LFR)** let concurrent transactions register qualifying numeric deltas against a `RESERVABLE` column without holding the normal row lock throughout the transaction. Oracle tracks pending deltas in a reservation journal, checks constraints against reservations, and applies the changes at commit with a short lock. It is **not** lock-free for arbitrary row modifications.

## 2. How did we solve this before?

A conventional `SELECT ... FOR UPDATE` locks a row before making a business decision. Even an atomic conditional `UPDATE` normally takes a row lock until commit. This is correct, but hot inventory or balance rows can become bottlenecks.

```sql
CREATE TABLE stock_regular (
  product_id NUMBER PRIMARY KEY,
  available NUMBER CONSTRAINT stock_regular_ck CHECK (available >= 0)
);
INSERT INTO stock_regular VALUES (101, 3);
COMMIT;

-- Session A:
UPDATE stock_regular SET available = available - 2
 WHERE product_id = 101 AND available >= 2;
-- Leave A uncommitted.

-- Session B (different connection):
UPDATE stock_regular SET available = available - 1
 WHERE product_id = 101 AND available >= 1;
-- B normally waits for A's row lock; A must COMMIT or ROLLBACK.
```

**Important:** The conditional predicate is already an excellent correctness technique: it avoids overselling when properly checked. The motivation for LFR is *reducing lock contention*, not making an unsafe decrement safe for the first time.

## 3. What is different? Two-session demonstration

Run the following **independently** from the ordinary-table demo:

```sql
CREATE TABLE stock_reserved (
  product_id NUMBER PRIMARY KEY,
  available NUMBER RESERVABLE
    CONSTRAINT stock_reserved_ck CHECK (available >= 0)
);
INSERT INTO stock_reserved VALUES (101, 3);
COMMIT;

-- Session A: reserve two units; do not commit yet.
UPDATE stock_reserved
   SET available = available - 2
 WHERE product_id = 101;

-- Session B, while A is open: reserve one unit.
UPDATE stock_reserved
   SET available = available - 1
 WHERE product_id = 101;
COMMIT;

-- Session A:
COMMIT;
-- Final available = 0.
```

**What Oracle enforces at runtime:** The qualifying `column = column - expression` operation creates a reservation entry. Oracle accounts for outstanding reservations when checking `available >= 0`. If Session B tries to reserve **two** instead of one, the combined demand (2 + 2) exceeds the three available units and its reservation fails rather than allowing negative stock. The app must handle the constraint/reservation error and roll back or reject the purchase.

| Moment | Ordinary row locking | Lock-Free Reservations |
|---|---|---|
| A decrements and remains uncommitted | A holds row lock | A registers pending numeric delta |
| B decrements same product | Typically waits | Eligible reservation can proceed |
| Total requested exceeds available | Conditional update/check prevents oversell | Reservation-aware check prevents oversell |
| Commit | Releases row lock | Briefly locks row to apply reserved delta |

**Coaching prompts:** “Do we need to hold a row lock while a payment service is called?” “What happens if three units exist and two shoppers each request two?” The answer should emphasize *business constraints still enforced* and *shorter lock duration*, not unlimited parallelism.

**Restrictions to call out:** `RESERVABLE` is for supported numeric columns; the table needs a primary key; reservable updates must be increments/decrements identified by key, not `SET available = 0`; you cannot mix reservable and non-reservable column changes in one update. A transaction that also changes ordinary columns can still acquire conventional locks. Never promise a speedup without contention measurements.

## 4. What are the advantages and limitations?

**Advantages:** can reduce hot-row waiting for high-volume inventory, balance and counter deltas; database enforces declared bounds with outstanding reservations. **Costs:** narrower DML semantics, journal/commit processing, operational restrictions, and application error handling. Conventional locking is more flexible and may be simpler for low-contention workloads.

## 5. When should developers adopt it?

**Adopt** when production evidence shows many concurrent numeric increments/decrements on the same rows and row-lock waits are material. **Keep conventional locking** for general edits, coordinated updates to multiple attributes, or low contention. Start with a benchmark using two or more sessions and real transaction durations.

## Key takeaway

**An atomic update protects correctness; Lock-Free Reservations target the waiting time caused by hot-row locking.**

## Documentation — Oracle AI Database 26ai

- [Using Lock-Free Reservation](https://docs.oracle.com/en/database/oracle/oracle-database/26/adfns/using-lock-free-reservation.html)
- [SELECT (including FOR UPDATE)](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/SELECT.html)

# Transactions & Concurrency

## Presenter purpose
Show that Oracle offers **different transaction mechanisms for different bottlenecks**: hot numeric rows, long application interactions, priority conflicts, distributed business workflows, and reliable event publication. Do not imply one feature replaces the others.

## Introduction — why developers should care
A transaction can be correct with one user yet behave poorly under contention. Inventory counters become hot rows; connection pools are tied up while people think; important work waits on locks; and a business operation may span services that cannot share a single database rollback. These are architectural problems as much as SQL problems.

## The capabilities and what to notice

### Lock-Free Reservations — contention on a numeric resource
Traditional updates to the same inventory row can serialize behind a row lock. A **RESERVABLE** numeric column uses reservation semantics for suitable additive changes, reducing conventional hot-row blocking. It is not a general-purpose lock removal mechanism. Availability constraints and concurrent reservations still need enforcement; the outcome of competing requests matters more than a simplistic promise that no one waits.

**Coaching scenario:** Ten units are available. Two sessions try to reserve eight and three. Both cannot ultimately consume eleven. Oracle considers outstanding reservations when checking a new request; with 10 available, Session 1 reserving 8 leaves insufficient projected availability for Session 2 to reserve 3. The second UPDATE should be rejected by the constraint, rather than deferring the oversubscription error to commit. The first reservation remains available to commit. Verify the observed error on the target database. This is a good discussion of correctness under load, not a benchmark.

### Sessionless Transactions — transaction lifetime versus connection lifetime
A web application may start work, return control to a user, and resume later. Sessionless Transactions let a transaction be started, suspended, and resumed using its identifier so a connection need not remain occupied for the entire interaction. They are about **session utilization and application workflow**, not lock-free numeric updates.

### Transaction Priorities — important work behind a lock
Configured priority policies can influence handling of selected conflicts when lower-priority transactions hold locks. This is different from reservable columns or sessionless work; the policy must match operational requirements.

**Application error handling after priority rollback:** When Oracle automatically rolls back a lower-priority blocker, the transaction changes have already been undone, but its session remains connected. A subsequent statement can raise `ORA-63302` (referencing `ORA-63300`). The application must issue an explicit `ROLLBACK` to acknowledge the automatic rollback before continuing. This acknowledgment does not undo the work twice. Retry policy remains an application responsibility.

### Saga support — a business transaction across services
A Saga is a sequence of locally committed steps with **compensating actions** if later steps fail. Think flight, hotel, and rental car booking. If the hotel booking fails after the flight commits, an ordinary rollback cannot reverse that separate commitment; the business workflow must cancel or compensate. Oracle provides Saga support, while application teams define the business steps and compensation logic.

### Transactional Event Queues (TxEventQ) — commit data and event together
An order may commit while the application crashes before publishing `order placed`; or an event may be published before the order rolls back. Enqueue work in TxEventQ can participate in the same database transaction so event visibility follows commit. TxEventQ also offers partitioned event streams, concurrent consumers, and Kafka-compatible interfaces for integration. This is an evolution of Advanced Queuing, not an automatic migration mandate or a substitute for all Kafka deployments.

## Demo coaching
`transactions_concurrency_demo_config.sqlnb` checks administrator-controlled Priority Transaction parameters and optionally sets a short wait target. Session 1 prepares the three demonstration tables. `transactions_concurrency_demo_session_1.sqlnb` and `transactions_concurrency_demo_session_2.sqlnb` alternate through Lock-Free Reservations (8 + 3 against 10), Sessionless Transaction handoff and Priority Transactions. The original `transactions_concurrency_demo.sqlnb` remains an unchanged fallback. Priority Transactions are optional if ADB Free disallows the system settings. The admin cleanup script restores the captured original values; do not assume defaults. Use Saga and TxEventQ as **architecture awareness** topics supported by the surrounding slides; do not suggest the notebook demonstrates an end-to-end booking system or Kafka consumer.

## Close-out — the memorable point
Choose the mechanism for the actual problem: reservation contention, connection utilization, transaction priority, distributed compensation, or reliable event publication. The database can take responsibility for more of that coordination, but application behavior and failure handling still need deliberate design.

**Assets:** `transactions_concurrency_demo.sqlnb` (fallback), `transactions_concurrency_demo_config.sqlnb`, `transactions_concurrency_demo_session_1.sqlnb`, `transactions_concurrency_demo_session_2.sqlnb`, `transactions_concurrency_cleanup.sql`, `transactions_concurrency_admin_cleanup.sql`. **Related notes:** comparisons in `additional_information/`, including TxEventQ vs. Advanced Queuing.


## Validated execution observations (ADB Free)

- Lock-Free Reservations: Session 1 reserved 8 of 10 without committing; Session 2 attempted 3 and received ORA-02290 at UPDATE. After Session 1 committed, 2 remained.
- Sessionless Transactions: Session 1 started and suspended the transaction; Session 2 resumed using the same GTRID and committed. Session 1 then observed the committed change.
- Transaction Priorities: with ROLLBACK mode and 5-second HIGH wait target, the LOW-priority blocker was rolled back and Session 1 subsequently received ORA-63302 referring to ORA-63300; Session 2 committed the HIGH-priority update.

These are observed outcomes from one tested environment; administrative priority settings and supported behavior must be checked on each target instance.

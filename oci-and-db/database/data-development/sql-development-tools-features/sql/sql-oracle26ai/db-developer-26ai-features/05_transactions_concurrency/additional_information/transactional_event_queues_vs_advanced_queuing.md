# Transactional Event Queues vs. Advanced Queuing

> **Developer question:** Oracle Advanced Queuing already provides reliable transactional messaging. What bottleneck does Transactional Event Queues address, and when is switching justified?

## 1. What is the new capability?

**Transactional Event Queues (TxEventQ)** is Oracle's partitioned, high-throughput event-queue implementation. Like **Advanced Queuing (AQ)**, it stores messages in the database and supports transactional enqueue/dequeue, subscribers and asynchronous processing. It is not a replacement for database transactions or a claim that every queue must be migrated.

The important change is **how a busy queue scales**, especially when many sessions publish and consume on multiple Oracle RAC instances. TxEventQ uses independently processed event streams, managed partitions and a specialized in-memory message cache.

## 2. How did we solve this before?

With traditional AQ, an application enqueues a message as part of its business transaction, and one or more consumers dequeue it. This is a proven approach for background work, workflow steps, notifications and reliable integration. AQ already supports multiple consumers and concurrent dequeues; it is **not inherently single-threaded**.

**Coaching scenario — the existing queue works until traffic grows:** A service publishes order-status events and several workers consume them. At moderate traffic, AQ is sufficient. As publishers and consumers are added across RAC nodes, contention may develop around the *head and tail* of the queue, its underlying queue-table/index structures, and repeated message reads. Adding more workers does not guarantee linear throughput growth.

This is a **conceptual workload**, not a benchmark or an executable order-processing demo.

## 3. What is different?

| Design question | Traditional Advanced Queuing | Transactional Event Queues |
|---|---|---|
| Can messages participate in database transactions? | Yes | Yes |
| Can multiple consumers dequeue concurrently? | Yes | Yes; event streams provide an additional parallelism mechanism |
| Where can contention arise? | Shared queue head/tail, queue table and index access, particularly across RAC instances | Streams and automatically managed partitions reduce competition among enqueuers/dequeuers |
| How are message payloads accessed? | Persistent queue storage; some optimizations and buffering are available | Specialized Streams-pool message cache can avoid disk rereads on dequeue |
| Ordering | AQ supports ordering choices and queue semantics | Ordering within an event stream/session; **not** a global total order across streams |
| Primary reason to choose | Mature workflow messaging and existing AQ-specific capabilities | Higher-throughput event streaming with parallel consumers, particularly on RAC |

### Where does the scalability gain come from?

**1. Less hot-spot contention.** Oracle documents that traditional AQ queue entry/exit points can become hot spots. With TxEventQ, managed partitioning separates event streams so multiple enqueue and dequeue sessions need not contend for the same queue structures in the same way.

**2. Parallel work on one logical queue.** TxEventQ permits messages from different enqueue sessions/event streams to be dequeued in parallel. This is especially relevant to a *single queue shared across RAC instances*, where adding consumers to traditional AQ may expose shared hot spots.

**3. Less repeated storage work.** TxEventQ's message cache holds payloads in the Streams pool; a cache hit can avoid rereading the payload from disk. Oracle also describes optimizations that reduce some queries, DML and index work. This exchanges **SGA memory** for potential throughput and latency improvement.

**Coaching illustration — two consumers:** Imagine event stream A carries customer A's events and stream B carries customer B's. Consumer 1 can work on A while consumer 2 works on B. Both progress independently, but the application **must not assume** that an event on A is globally ordered relative to an event on B. This illustrates the concurrency model, not a measured performance result.

### What proof should a skeptical developer look for?

Oracle's **26ai Performance and Scalability** chapter explicitly identifies the hot-spot problem in AQ and explains the TxEventQ partitioning/cache mechanisms. It is architectural evidence for *why* scalability can improve, **not proof of a specific speedup for your workload**. A defensible evaluation measures sustained messages/second, enqueue-to-dequeue latency (including p95/p99), backlog growth, RAC contention/waits, CPU/I/O and Streams-pool use under the same producer/consumer load. Increase concurrent producers and consumers and compare the scaling curves; do not quote a generic percentage without a reproducible benchmark.

## 4. What are the advantages and limitations?

**Advantages:** More parallelism for a heavily shared queue; reduced queue-structure contention; caching that can lower dequeue I/O; improved scalability on multi-instance RAC workloads. Existing database transactional integration remains an advantage of *both* approaches.

**Limitations and trade-offs:** TxEventQ uses additional Streams-pool memory, and slow consumers can erode cache benefits. Cross-stream ordering is not guaranteed. TxEventQ does not support every AQ feature: Oracle lists restrictions including message transformations, transaction grouping, Messaging Gateway, some JMS extensions/propagation patterns, and propagation between TxEventQ and AQ. Confirm client-driver compatibility and any application reliance on queue-specific features before migration. More consumers do not help if downstream processing is the actual bottleneck.

**Operational coaching point:** Oracle documents `GV$AQ_MESSAGE_CACHE_ADVICE` and Streams-pool tuning for TxEventQ. This makes cache sizing and consumer lag part of the scalability discussion rather than an invisible implementation detail.

## 5. When should developers adopt it?

**Consider TxEventQ** when one logical queue serves many producers and consumers, throughput plateaus as concurrency increases, RAC queue hot spots are measurable, or an event-streaming design needs parallel subscribers.

**Keep AQ** when existing transactional messaging meets throughput and latency requirements, when ordered workflow or AQ-specific functionality matters, or when migration effort outweighs measurable gains. Do not migrate simply because TxEventQ is newer.

**Practical decision:** First identify the bottleneck. If the limiting factor is queue-table/index contention, repeated message I/O, or RAC hot spots, TxEventQ is a credible candidate. If the limiting factor is slow application processing, network calls or an overloaded downstream service, changing the queue implementation alone will not fix it.

## Key Takeaway

**AQ already provides transactional messaging and concurrency. TxEventQ changes the scaling architecture:** event-stream partitioning and a message cache can reduce contention and repeated storage work, particularly for busy queues across RAC. Evaluate the benefit with your own workload and check unsupported AQ features before migrating.

## Documentation

- [Transactional Event Queues — Oracle AI Database 26ai: Performance and Scalability](https://docs.oracle.com/en/database/oracle/oracle-database/26/adque/aq-performance-scalability.html) — includes TxEventQ internals, AQ queue hot spots, tuning guidance and restrictions.
- [Advanced Queuing — Oracle AI Database 26ai: Introduction](https://docs.oracle.com/en/database/oracle/oracle-database/26/adque/aq-introduction.html) — describes the existing AQ messaging model and capabilities.

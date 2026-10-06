# Choose where truth lives

## Put each invariant beside its authority

An invariant is a rule that must hold across a change: an order cannot be both cancelled and fulfilled; a pickup window cannot exceed its confirmed capacity; a refund cannot exceed the amount collected. If multiple processes can update the facts that enforce the rule, those processes need a coordination mechanism.

The simplest strong boundary is often one transaction in one authoritative store. A conditional update such as “reserve one place only if remaining capacity is greater than zero” can serialize competing requests at the point where the decision is made. A version check can reject stale edits. A unique constraint can prevent duplicate external IDs even if application code races.

Move the invariant outward only when there is a concrete need. Splitting ownership across services may improve team autonomy or isolation, but it turns a local atomic change into a workflow. The workflow must represent intermediate states, retry decisions, and compensation. That is a meaningful architectural cost, not merely a network call replacing a function call.

## Choose a concurrency strategy

**Pessimistic coordination** prevents simultaneous work from proceeding through a contested section, often by locking a record. It is easy to reason about when contention is modest and transactions are short. Long-held locks reduce throughput and can cause deadlocks, so keep the critical section narrow and define a timeout.

**Optimistic coordination** lets work proceed and checks at commit that the data has not changed. A revision number or compare-and-set condition can detect a conflict. It works well when conflicts are uncommon; frequent conflicts turn repeated retries into waste. Clients need a clear conflict response and a safe way to reload or merge.

**Single-owner serialization** routes all decisions for one key through one authority. It makes per-key ordering straightforward, but a hot key can become a bottleneck and the owner needs a failover story. It does not automatically provide global order across every key.

There is no universally best approach. The cost of a false acceptance, a rejected request, and a delayed request differs by domain. Choosing a strategy means choosing which outcome is acceptable under contention.

## Treat network uncertainty as normal

A distributed service can be healthy while a particular request times out. A timeout limits how long a caller waits; it does not cancel work already accepted elsewhere. Retries can multiply load precisely when a dependency is struggling. Use bounded retries with backoff and jitter, respect idempotency keys, and place deadlines across the call chain so work does not continue long after the user has left.

A circuit breaker or load shedder can prevent repeated calls to a dependency that is already failing. It should fail in a way the product can explain. If browsing can continue but confirmation cannot, expose that distinction instead of declaring the whole service either “up” or “down.” A graceful degraded mode must not accidentally make a stronger promise than the normal mode.

## Know what “consistent” means here

Different operations may need different visibility guarantees. A user who submits an order and immediately opens its receipt usually expects read-your-writes: their own committed change is visible. A public browse page may tolerate a short delay. A support report might need a stable snapshot so multiple pages tell one coherent story.

Name the consistency behavior for each path. Does a read come from the leader, a replica, or a projection? Can a recently committed update be temporarily absent? Does a response include a revision that the client can use to request at least that version? Precise language turns an abstract debate into a product contract.

When replicas are distributed across a network, a partition can separate nodes that can no longer communicate. If both sides accept conflicting updates, the system needs a conflict rule later. If only one side may make the decision, the other side must reject or delay some writes. This trade-off is not erased by a clever slogan. Decide which behavior is safe for the business operation.

## Use conflict resolution only when the domain supports it

Some concurrent changes merge naturally. Two devices adding separate items to a shopping list can preserve both additions. A text field edited differently on two devices may need a human choice. Inventory reservations do not safely merge by summing two local “available” counts if doing so can oversell stock.

Automatic merge rules are business rules. State them in domain language, test them under duplicated and reordered updates, and preserve enough history to explain the result. If no principled merge exists, choose one authority or surface the conflict instead of silently picking a winner.

> **Design check:** Name one invariant in your system. Which component is the final authority when two valid-looking requests try to change it at the same time?

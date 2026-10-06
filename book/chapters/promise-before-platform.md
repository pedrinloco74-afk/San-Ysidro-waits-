# Promise before platform

## Start with the sentence a customer can understand

A team says, “We need a scalable order system.” That sentence contains a wish, not a design. Scalable for which workload? What does an order mean when a phone loses its connection after payment? Is a one-second-old stock count acceptable, or can it cause a customer to arrive for groceries that do not exist?

Begin with the promise the product needs to keep. A useful promise is observable from outside the system and specific enough to test. For a neighborhood pickup service, it might read: **Once we confirm an order, we will keep its pickup slot and either provide every confirmed item or contact the customer before pickup.** That statement is not a database choice. It is a boundary for every database choice that follows.

Promises often contain several dimensions that teams accidentally bundle together:

- **Correctness:** which outcomes must never happen? A confirmed order must not silently disappear.
- **Freshness:** how old may a displayed fact be? A browse page may lag by a few seconds; a final stock reservation may not.
- **Availability:** which operations should remain possible during a dependency failure?
- **Latency:** how long may a person reasonably wait for each operation?
- **Durability:** what does “saved” mean, and what failures must it survive?

These are separate dials. “Highly available and strongly consistent” is not yet a useful requirement; it leaves out which operation, during which failure, with what response. Put the promise next to the operation that makes it real.

## Make the invisible measurable

Turn each promise into a small contract. A contract names the actor, action, outcome, and acceptable time or error boundary. For example:

| Operation | User-visible outcome | Target |
| --- | --- | --- |
| Browse a pickup window | Show an estimate and its update time | p95 under 350 ms; at most 10 seconds old |
| Submit an order | Return a durable confirmation or a clear retry-safe failure | p95 under 800 ms |
| Cancel before cutoff | Release the reservation exactly once from the customer's point of view | Complete within 2 seconds |
| View an order after submit | Show the confirmed items and pickup slot | Available immediately from the write path |

The exact numbers are product decisions, not universal benchmarks. A team should be able to explain why a number exists and what a customer experiences when it is missed. A percentile is more revealing than an average: averages can hide a long tail of people waiting while most requests finish quickly. Track error rates and freshness alongside latency; a fast answer with stale inventory can be worse than a slower, honest answer.

A service-level indicator is the measurement. A service-level objective is the target. An error budget is the amount of tolerated miss over a window. These terms are useful only when connected to a decision: if the freshness objective is repeatedly missed, should the team reduce promotional traffic, simplify the browse view, or invest in a faster projection pipeline?

## Draw the boundary of a promise

A system cannot promise what it does not control. If pickup depends on a partner's inventory feed, separate the promise for the catalog estimate from the promise for a confirmed reservation. Display uncertainty honestly. “Usually available” and “reserved for you” must not be the same state with different colors.

Write down the failure behavior, not only the happy path. What does the customer see when the payment provider times out? What if the service commits the order but its response never reaches the browser? A timeout means the caller did not learn the outcome; it does not prove the operation did not happen. Designing a safe retry is part of keeping the promise.

For every critical operation, record:

1. The invariant that must hold.
2. The authority allowed to decide it.
3. The durable point after which success may be reported.
4. The user-visible behavior when that point cannot be reached.
5. The signal operators use to notice a miss.

This tiny checklist is often more valuable than an early diagram of ten services. It exposes incompatible expectations while they are still cheap to change.

## Let evidence choose the machinery

Only now ask what workload the system must support. Estimate reads and writes per second, typical and worst-case record sizes, retention, bursts, and geographic reach. Separate current traffic from plausible growth. A system designed for a fantasy workload is not safer; it merely adds more moving parts before anyone can measure their value.

Start with the simplest arrangement that can honor the contract. A single transactional store may handle years of traffic. A cache, queue, search index, or partitioned cluster earns its place when a measured pressure or a clear failure boundary calls for it. Each additional component creates a new place where data can be delayed, duplicated, unavailable, or misunderstood.

The point is not to prefer small systems forever. It is to make complexity answer a question. When the question changes, revisit the design. The platform follows the promise; the promise does not have to imitate the platform.

> **Design check:** Can a support engineer explain, in plain language, when an order is merely requested and when it is genuinely confirmed?

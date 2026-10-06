# Build the read you actually need

## A read path is part of the product

A product may store orders correctly and still feel unreliable if the customer cannot see the confirmed order, the picker cannot find the list, or support cannot explain what happened. Reads shape trust. Design them from the questions each person asks, not from whichever storage format happens to be convenient.

List the screens and decisions first. A shopper browsing a pickup window needs a compact availability estimate. A customer viewing a receipt needs the exact items and terms that were confirmed. A picker needs an ordered work list grouped by location. An analyst needs history across many weeks. These are different queries with different freshness and latency requirements.

One data model rarely serves all of them equally well. That is acceptable. Keep one clear authority for changes, and create read-optimized representations where measurements justify them. A projection can flatten related information, precompute totals, or group work for a specific task. It is a view of facts, not a second, competing authority.

## Choose between live reads and projections

A live query reads current authoritative records at the moment of the request. It is useful when the result must reflect the latest committed state and the query remains efficient. As relationships and request volume grow, a live query may require many lookups or expensive aggregation.

A projection is updated after changes occur. It can make reads fast and simple, but it introduces a delay and another lifecycle to operate. The design should name that delay as a freshness contract rather than describing the view as “real time.” If a dashboard usually catches up in two seconds but can take thirty during a backlog, tell the user what the displayed timestamp means and alert on lag.

A projection consumer should be restartable. It needs a checkpoint, a way to replay changes, and a strategy for rebuilding from authoritative data. If a projection cannot be reconstructed, it is not merely a convenience; it has become a hidden source of truth.

## Make stale data safe

Stale reads are not always dangerous. A product description can be minutes old without harming a transaction. A stock estimate can also be stale while browsing, provided the final reservation rechecks current availability. The key is to put the authoritative decision at the point where an irreversible promise is made.

Useful patterns include:

- Display a freshness timestamp for data that changes often.
- Label estimates differently from confirmed values.
- Revalidate critical preconditions at submit time.
- Return a version with the view so a later command can detect that it is outdated.
- Design the UI to recover gracefully when a final check rejects an optimistic estimate.

This allows the system to use fast, eventually refreshed views without pretending they are exact. The user sees the boundary between a helpful preview and a committed decision.

## Cache with a reason

A cache reduces repeated work by keeping a copy close to the reader. It can improve latency and absorb bursts, but it adds another place to reason about freshness, memory limits, eviction, and failure. Cache only after measuring a bottleneck or identifying a cost worth avoiding.

For mostly immutable content, use versioned keys or long cache lifetimes. For mutable values, decide what event invalidates the cache, how missed invalidations are repaired, and what happens when the cache is empty. If a cache miss overloads the database, request coalescing or a brief fallback may be necessary. If the cache is unavailable, the system should either continue at reduced speed or fail clearly; it should not accidentally turn a recoverable cache problem into a total outage.

Be cautious with a cached answer that controls a scarce resource. It may be fine to show “about six boxes remain,” but a cached value should not authorize the sixth and seventh reservations simultaneously. The authoritative store must enforce that invariant.

## Make pagination stable

Large lists should be read in bounded pages. Offset-based pagination is easy to understand but can become expensive and unstable when records are inserted or removed between requests. Cursor pagination uses a stable ordering and returns a marker for the next page. A useful cursor includes all ordering fields, for example creation time plus a unique order ID, so ties do not cause records to disappear or repeat.

For a snapshot-like experience, bind pages to a consistent revision or timestamp when the storage system supports it. For a live activity feed, explain that new entries may appear above the current cursor. Pagination is a product behavior as much as a query trick.

## Instrument the answer, not just the database

Measure end-to-end read latency, result size, cache hit rate, projection lag, and error rate. Track the freshness of the data presented to the user, not just the time taken to retrieve it. A fast query over a projection that stopped consuming yesterday is a successful database request and a failed product experience.

> **Design check:** Which displayed values may be estimates, and where does the system recheck the fact before promising something costly or irreversible?

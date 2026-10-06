# From promise to running system

## The scenario: Mesa Market

Mesa Market is a fictional neighborhood food co-op with several pickup locations. Members browse weekly offerings, place an order, choose a pickup window, and collect a packed bag. The team is small. It needs a design it can operate before it needs a design that survives internet-scale traffic.

The first promise is deliberately narrow: **A confirmed order has a stable item list and pickup window. Mesa Market will not confirm more reservations than a location can fulfill. If a final check fails, the customer sees a clear alternative before the order is confirmed.** Browse quantities are estimates; the confirmation step is authoritative.

The promise identifies two different read and write paths. Browsing can use a refreshed projection. Confirmation must check the current reservation state. That one distinction keeps a fast browse page from pretending to reserve stock.

## Choose the first authoritative boundary

Start with a relational database for the core records. This is not a claim that one database is always right; it is a reasonable first fit for related records and transactional invariants. The initial model includes:

- `pickup_window`: location, start time, capacity, and active state.
- `reservation`: window, order ID, quantity, and lifecycle state.
- `order`: member, selected window, confirmation state, and idempotency key.
- `order_line`: product ID plus a snapshot of name, unit, price, and quantity.
- `outbox`: event ID, order ID, event type, version, and publication state.

A request to confirm an order opens a short transaction. It verifies the window is open, conditionally increments its reserved quantity only if capacity remains, inserts the order and its lines, and records an `OrderConfirmed` outbox event. A unique constraint protects the idempotency key. If any precondition fails, the transaction commits no partial order. The service returns a confirmation only after the database reports a durable commit under the chosen configuration.

This design places the scarce-window invariant beside its authority. It also preserves what the member agreed to, even if catalog details change later. The implementation should test two simultaneous requests competing for the last place; a unit test of the happy path is not enough.

## Add read models where they pay off

The member's order receipt can read the authoritative order record. The browse page needs a product and availability summary, so a small projection worker consumes catalog and reservation events and writes a denormalized browse view. Each view row includes an update time. The page labels availability as an estimate, and confirmation rechecks the reservation transaction.

An operations view can be another projection grouped by pickup window, showing confirmed item counts and packing status. It does not get to alter the order's confirmed lines. If it falls behind, the freshness metric alerts and the page shows “updated at” rather than quietly presenting an old count as current.

For the first release, both projections can live in the same database if load is modest. The data contract and rebuild process matter more than a premature choice of separate technology. A rebuild command reads authoritative records in batches, replaces the projection safely, and tracks progress. The team can later move a projection to a dedicated search or analytical system without moving the authority for confirmations.

## Make side effects durable and repeatable

The outbox publisher sends `OrderConfirmed` to a message broker. A receipt worker and the operations projection consume it independently. Every event has a stable ID and order version. If the publisher sends twice, consumers recognize the duplicate. If a consumer fails, the message remains retryable; after bounded retries, it is quarantined with an alert and a replay procedure.

The confirmation response does not wait for an email. The durable order is the confirmation; the email is a follow-up. The order page displays its current state directly from the authoritative record, so a delayed receipt cannot make the order disappear. A status page can distinguish “order confirmed” from “receipt email sent.”

If a payment provider participates, give that interaction its own state. A timeout from the provider is not the same as a decline. Use the provider's idempotency mechanism and reconcile uncertain attempts. Do not reserve a pickup window indefinitely while the outcome is unknown; define a reservation expiry and a visible pending state. The exact sequence depends on whether the co-op collects payment at checkout or at pickup, which is a business decision rather than a database preference.

## Add capacity only when the evidence asks

Suppose traffic grows. First measure what is saturated: database connections, a hot pickup window, projection lag, or a slow product query. Add an index or connection pool adjustment only when evidence supports it. Cache stable catalog details if repeated reads dominate. Increase worker concurrency only if the broker backlog is growing and the database has headroom.

If several locations grow independently, location may be a useful operational partition for reservation work. But a member's order history then spans locations, so it may need a separate read model. A single pickup window remains a hot key during a popular release; exact capacity still requires one authority for that window. If contention becomes substantial, queue reservation commands by window or move that decision to a dedicated owner. Test the ordering and failover behavior before changing the promise.

None of these changes requires the browse projection to become authoritative or the entire application to be split into services. Keep the invariant and its owner stable while changing the paths around it.

## Rehearse the uncomfortable cases

Before launch, test these scenarios:

1. The client times out after a successful commit, then repeats the request with the same key.
2. Two members request the last pickup place at the same moment.
3. The database commits the order, but the outbox publisher is offline for twenty minutes.
4. The projection worker sees the same event twice and later receives a newer version first.
5. A backup is restored and the browse view is rebuilt from authoritative records.
6. The payment provider accepts a charge but its response is lost.

Each test needs a defined customer result, a durable system state, and an operator signal. If the team cannot describe one of those, the design is not finished.

## The compact blueprint

Mesa Market's first dependable version is not dependable because it uses a long list of technologies. It is dependable because its promises map to explicit boundaries:

- A transaction owns order confirmation and pickup capacity.
- An idempotency key makes uncertain retries safe.
- An outbox records follow-up work with the business change.
- Consumers can handle duplicates and expose their lag.
- Projections speed up reads but never authorize reservations.
- A recovery drill proves that core data and useful views can return.

That blueprint can begin as one application and one database. It can later gain queues, partitions, replicas, or service boundaries as real constraints appear. The shape may change; the promise remains the compass.

> **Final design check:** Can every “confirmed” message in the product be traced to a durable decision, and can the team prove that by exercising the failure paths?

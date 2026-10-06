# Give every fact a home

## Model the meaning before the container

Storage discussions tend to begin with nouns: table, document, key, cache. Begin instead with the facts the business recognizes. In a pickup service, an order has a customer, a chosen window, a set of requested items, and a lifecycle. A pickup window has a capacity. An item has a catalog description and may have separate quantities at multiple locations.

A model is a set of claims about the world. Good models make important rules easy to state and hard to violate. If a reservation is for one item at one location, represent those dimensions explicitly. If “available quantity” is derived from counted stock minus active reservations, decide whether it is stored as a number, computed on demand, or maintained as a projection. Every representation is a bet about which update must be easy and which mistake must be prevented.

A practical first pass is to list:

- **Entities:** things with identity and a lifecycle, such as an order or pickup window.
- **Events:** facts that happened, such as an order being confirmed or a reservation being released.
- **Values:** descriptive details that are meaningful only in context, such as an address snapshot on an order.
- **Invariants:** conditions that must be true across a change, such as a window never exceeding its confirmed capacity.

The same word can describe more than one concept. “Inventory” might mean a count from a supplier, units physically checked in, units promised to orders, or an estimate shown to browsers. Give each meaning a name. Ambiguous nouns eventually become ambiguous columns and contradictory dashboards.

## Assign authority, not just ownership

For every important fact, name the component that is allowed to change it. The catalog may own product descriptions; the reservation service may own claims on available stock; the order record may preserve what the customer actually bought. Ownership is about decision rights, not merely which team maintains a table.

This matters when a fact is copied. A browse index can hold product names for fast searching, and an analytics warehouse can hold historic order lines. Those are useful copies, but they should not quietly become authorities. If a copied value disagrees with the owner, the design needs a known path to refresh it and a rule for what the user sees in the meantime.

Name the answer to three questions:

1. Where is the authoritative version of this fact?
2. Who may change it, and under which rule?
3. Which copies exist, how are they refreshed, and how stale may they be?

This is the beginning of a data contract. It prevents a common organizational failure: two services both believe they are entitled to make the final decision.

## Give identity a lifetime

Identifiers should survive the movement of data between screens, processes, and storage systems. A stable order ID is not the same as a customer's email address, a database row number, or the order's current position in a list. Use opaque identifiers when the value crosses trust boundaries; avoid exposing sequential IDs if they reveal business volume or invite enumeration.

Identity also needs scope. A product code may be unique within one co-op but not across every co-op in a network. A pickup window might be identified by location and start time, but that pair becomes awkward if schedules change. Choose an ID that represents the entity's lifetime, then store mutable attributes separately.

For records that can be edited concurrently, keep a revision or update token. A request can say “change this address if the order is still at revision 12.” If another change already produced revision 13, the system can reject the stale edit rather than erase it. Versioning is a simple, visible tool for expressing the rule “do not overwrite a change you did not see.”

## Treat schemas as agreements over time

Stored data outlives the code that first wrote it. Renaming a field is not a local refactor when old application versions, delayed messages, exports, and backups still contain the earlier shape. Prefer changes that remain understandable during a transition: add an optional field, teach readers to accept both versions, backfill in bounded batches, then make the new field required only after old writers have gone away.

A safe migration often has four stages:

1. **Expand:** add a new representation without removing the old one.
2. **Dual-read or dual-write selectively:** bridge old and new clients while monitoring disagreement.
3. **Migrate:** copy historical data in restartable batches, with a checkpoint and rate limit.
4. **Contract:** remove the old path only after the rollback window closes.

Not every change needs all four steps, but every change should answer what happens if deployment stops halfway. A migration that only works when all servers update simultaneously is fragile in a rolling deployment.

A schema describes bytes; a data contract describes meaning. Record both. Include units, time zone, null semantics, valid state transitions, and who is permitted to write. “Amount” without currency and “date” without time zone are not complete facts.

## Preserve what the customer meant

Some data is a live reference; some is a historical snapshot. An order line should usually preserve the product name, unit price, and quantity as understood at confirmation time. If the catalog title changes tomorrow, an old receipt should not rewrite itself. Conversely, a shipping address may need both the original submitted value and the normalized value used by a delivery route.

Choose deliberately between a pointer to current truth and a snapshot of past truth. Many records need both. The distinction makes audits, support conversations, and later corrections far less mysterious.

> **Design check:** For each field in a critical record, can you name its meaning, authority, unit, and behavior after the underlying business object changes?

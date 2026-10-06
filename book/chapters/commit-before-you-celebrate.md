# Commit before you celebrate

## A request can have an uncertain ending

A browser sends “place this order.” The server validates it, commits the database transaction, and begins sending a response. The connection breaks before the browser receives that response. The order exists, but the customer sees a timeout. If the customer taps again, is the next request a duplicate order or a safe way to discover the first result?

This is one of the most important distinctions in distributed work: **a missing response is not evidence of a missing effect.** The caller knows only that it did not learn the outcome. A trustworthy write path must make uncertainty survivable.

A typical write has a sequence of meaningful stages:

1. Accept and validate the request.
2. Check authorization and business preconditions.
3. Apply the state change atomically with related facts.
4. Make the change durable under the promised failure model.
5. Return a result that names what was committed.
6. Publish follow-up work without creating a gap between the record and the message.

The exact implementation depends on the store, but the boundary must be clear. If the response says “confirmed,” identify the durable point that justifies those words.

## Make retries recognizable

A client-generated idempotency key gives repeated attempts a stable identity. The server stores the key with the result of the first accepted attempt. When the same key arrives again, it returns that result rather than performing the action twice. A key should be scoped to the caller and operation, have a retention period long enough for realistic retries, and be associated with a request fingerprint so that accidental reuse with different content is rejected.

Idempotency does not mean every operation is naturally safe to repeat. “Set quantity to 4” is different from “add 4.” “Reserve this window for order 8F…” is different from “reserve one more slot.” Prefer commands that name the desired state or a unique operation. For event-like actions, assign an event or command ID and record whether it has already been applied.

Suppose the co-op receives the same order request twice. A unique constraint on the idempotency key can make the database the final arbiter, even when two application servers race. The losing request reads the stored outcome. This avoids relying on a process-local cache, which disappears on restart and cannot coordinate independent servers.

## Define the durability boundary

Durability is not one universal checkbox. It depends on what failures the system promises to withstand. A local commit may survive a process restart but not the loss of the machine. A replicated commit can survive a machine failure but may still be lost if acknowledgements are returned before replicas persist the record. A remote backup can protect against a regional incident but may lag behind live writes.

Ask specific questions:

- After success is returned, what hardware or service failures may occur without losing the record?
- Does the write need to be copied to another machine, another zone, or another region before acknowledgment?
- How much recent work may be lost in the worst acceptable recovery scenario?
- How long may recovery take, and who has rehearsed it?

A stronger durability target may add latency or reduce the ability to accept writes during a network split. That trade is a product decision with operational consequences, not a contest to choose the most impressive setting.

## Keep related facts together

An order confirmation may need to create an order record, reserve a pickup slot, and record a message for downstream notifications. If these actions happen in separate systems, a crash can land between them. The order may exist without its notification; worse, the notification may go out before the order is durable.

Where one store can atomically update the essential facts, use a transaction for that boundary. For work that must reach another system, a transactional outbox is a useful bridge: write the business change and an outbox row in the same transaction, then have a worker publish the row. The worker may publish twice if it crashes after sending but before marking the row complete, so consumers must also recognize duplicate message IDs.

The outbox does not create one giant transaction across the network. It turns an invisible gap into explicit, retryable state. Monitor the age of the oldest unpublished item; a growing outbox is a symptom that the promise is drifting.

## Report outcomes honestly

Avoid a response that says “success” while critical work is merely queued unless the user understands what remains pending. Use explicit states such as `requested`, `confirmed`, `cancelled`, and `needs_attention`. State names should describe business reality, not infrastructure details such as “message sent.”

When an operation is still in progress, return a durable operation ID that the client can poll or subscribe to. Make a retry return the same operation. If the final outcome is rejection, preserve enough context to explain why and whether another attempt could succeed.

A well-designed write path does more than persist bytes. It gives the system and its users a stable answer after interruptions, duplicates, and delayed responses.

> **Design check:** If the client times out immediately after the database commits, can it safely retry and learn the original result without creating a second effect?

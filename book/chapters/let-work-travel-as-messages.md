# Let work travel as messages

## Separate the request from its aftermath

Some work should finish before the system acknowledges the user. Other work can happen later: sending a receipt, refreshing a search view, preparing a picker list, or updating an analytics feed. Moving follow-up work out of the request path can make the product more responsive and can isolate failures, but it also creates a new contract: the work is accepted now and completed later.

A message usually represents either a command—“send this receipt”—or a fact—“order 8F was confirmed.” Commands ask one owner to act. Facts announce something that has already happened. Mixing the two makes it unclear who may change the truth. A useful event name describes a completed business fact in the past tense; a command names an intended action.

The producer should publish only facts it can defend. The consumer should own how those facts affect its own state. A notification worker can decide how to format an email, but it should not decide whether an order was truly confirmed.

## Expect delay and duplication

A queue or log may deliver a message more than once. A worker can complete an action, crash before recording its checkpoint, then receive the same message after restart. A delivery system that advertises “at least once” is saying duplicates are possible while messages are retried until acknowledged; it is not saying every consumer action is magically safe.

Make the consumer idempotent. Store the processed message ID or use a natural uniqueness rule. If a notification should be sent once per order and notification type, record that key before or with the send workflow. For external providers that do not support idempotency, model the uncertainty and reconcile from provider receipts rather than assuming a timed-out request did nothing.

Ordering also needs a scope. A global order over every event in the company is expensive and often unnecessary. It may be enough to preserve order for changes to one order or one pickup window. Partition messages by the entity whose sequence matters, and include a version so the consumer can detect a gap or an out-of-order update.

## Use backpressure instead of wishful speed

If messages arrive faster than workers can process them, backlog grows. Adding more workers helps only when the work can be parallelized and the downstream dependency can absorb the extra load. Otherwise it moves the queue into a database or external service and makes the overload harder to control.

Watch queue depth, oldest-message age, processing rate, retries, and failures by message type. Age often better captures customer harm than depth: a million cheap analytics events may be harmless, while a few delayed pickup cancellations may be urgent. Apply rate limits, bounded concurrency, and prioritization where promises differ.

A worker should make progress in small, restartable units. Long jobs need checkpoints. Poison messages need a bounded retry policy and a quarantine or dead-letter path with enough context for diagnosis. A dead-letter queue is not a graveyard; assign an owner, alert on new entries, and define how repaired messages are replayed safely.

## Connect records to messages

Publishing an event directly after a database commit creates a gap. If the process crashes between the commit and publish, the record changes but subscribers never hear about it. If publish happens first, subscribers may act on a fact that the database later rejects.

An outbox, introduced earlier, records the event in the same transaction as the business change. A publisher moves outbox rows to the broker and can safely retry. Consumers still need idempotency, because the publisher may not know whether a previous send succeeded. The pattern does not eliminate failure; it makes recovery explicit at both ends.

For workflows across multiple owners, use a state machine with durable steps rather than pretending all participants share one transaction. A reservation workflow might request stock, wait for a confirmation, and either confirm the order or release the reservation if payment fails. Each transition should have a timeout, a retry rule, and a compensating action when appropriate.

## Keep contracts evolvable

A message can be sitting in a queue for hours or replayed months later. Include a schema version or design fields so new consumers can ignore additions. Make changes compatible during rollout: deploy readers that tolerate the new shape before producers send it. Avoid reusing a field with a different meaning; old records do not learn the new interpretation.

Keep payloads small and intentional. A message may include a stable entity ID, event ID, version, occurrence time, and the minimum facts the consumer needs. If a consumer fetches current state by ID, it may see a later version than the event describes. Choose between a self-contained event snapshot and a pointer to current state based on whether the consumer needs history or only the latest answer.

> **Design check:** If a worker receives the same message twice, what durable rule prevents the second delivery from producing a second business effect?

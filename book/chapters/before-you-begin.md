# Before you begin

## A note from Cesar

Systems work is often introduced as a tour of technologies: a database, a queue, a cache, a cluster. Those tools matter, but they do not explain why one design is trustworthy and another is not. The difference usually starts with a promise: what a person expects the product to do, what the system can prove it has done, and what happens when a dependency goes quiet at the wrong moment.

This guide is about that distance between intention and evidence. It follows a small set of practical questions: What does the customer believe? Which record is authoritative? When is a change durable? How stale may a read be? Who owns a delayed task? Where does a rule get enforced? Can the team recover when a machine, process, or assumption fails?

The examples use Mesa Market, a fictional neighborhood food co-op. It is intentionally ordinary. Orders, pickup windows, receipts, and inventory estimates are enough to reveal the hard parts without requiring a giant company or a specialized industry. The choices are not recipes to copy; they are examples of how to connect a product promise to a technical boundary.

## How to use this guide

Read the chapters in order if you are starting a system or revisiting its foundations. If you have a specific problem, jump to the chapter that matches it: retries and durable writes, read freshness, asynchronous workers, partition choices, coordination, or recovery. The final design walks through the ideas as one coherent service.

For each system you work on, try answering the design check at the end of every chapter. Write the answer down. If two people on the team give different answers, you have found a useful design conversation—not a failure of vocabulary.

This is an original, practical introduction, not a catalog of products and not a substitute for testing against your own workload. Start with the smallest arrangement that can keep the promises your users need. Measure where it falls short. Add complexity only when it buys a specific improvement you can observe.

— Cesar Pedrin

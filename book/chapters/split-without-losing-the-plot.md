# Split without losing the plot

## Scale the hot path, not the diagram

A system can grow in several different ways: larger records, more active users, heavier queries, bursts at particular times, or higher availability expectations. Scaling is not a single operation. Identify which resource is constrained before splitting a dataset or adding another service.

Partitioning divides a collection or stream into pieces that can be stored or processed independently. A partition key decides where each piece goes. A good key spreads ordinary work while keeping operations that need to coordinate close together. The correct answer depends on the invariant and traffic pattern, not just on the number of rows.

For a co-op ordering service, order history might be partitioned by a stable order ID, while reservations could be grouped by location and pickup window because capacity decisions happen there. An analytics export might use date ranges. There is no rule that every dataset needs the same key.

## Understand the shape of traffic

Average load hides hotspots. A popular item, one large customer, a flash sale, or a single pickup window can direct a large fraction of requests to one partition. This is skew. Adding partitions does not fix a key that funnels every request to the same place.

Measure both key frequency and resource use. A partition receiving many inexpensive reads may be fine; one receiving many contended updates may be saturated. Consider whether a hot read can be cached or replicated, whether a write can be queued, or whether the logical entity can be safely divided into sub-entities. Splitting a scarce-resource counter across shards is not safe if the product still promises an exact global limit without a coordination rule.

Hashing keys spreads unrelated records but makes range queries harder. Range partitioning helps scans over time or geography but can send new writes to the same newest partition. Composite keys can put frequently related work together while adding enough variation to reduce hotspots. Each choice makes some operations easier and others more expensive.

## Keep cross-partition work visible

A query that touches one partition can be fast and predictable. A query that fans out to many partitions needs coordination, merge logic, timeouts, and partial-result behavior. If a customer asks for one order by ID, route directly. If an analyst asks for all orders across every region, use a path designed for broad scans rather than forcing the transactional store to impersonate an analytical warehouse.

Transactions across partitions may require additional coordination and can reduce availability during network failures. Before asking for them, check whether the invariant can be placed inside one partition, expressed as a reservation workflow, or settled asynchronously with a clear pending state. Some global invariants really do require coordination; the goal is to make that cost explicit rather than accidentally paying it on every request.

## Plan for movement

Partition layouts change as traffic and storage grow. A migration may move records while reads and writes continue. A safe plan defines a routing epoch, tracks which version owns each key, and handles writes that arrive during the move. Depending on the system, this might mean copy-then-catch-up, temporary dual reads, or a service-managed rebalancing process.

Never assume that changing the number of hash buckets is a free configuration edit. It can remap a large share of keys. Keep data placement behind a routing layer or use a database whose rebalancing behavior is understood and observable. Test the movement with realistic key distributions and enough spare capacity to hold both old and new copies during transition.

## Separate workload classes

Transactional updates, interactive browse queries, background projections, and analytical scans compete for different resources. They may share infrastructure at first, but give each a clear budget. A batch report should not consume every connection needed by checkout. A queue worker should slow down when its downstream store is near saturation. A cache should not hide an unbounded fan-out query.

Capacity planning is a feedback loop: measure, forecast, test, and revise. Keep a representative load test that includes skew, cold caches, and downstream latency. Record what fails first. A system is easier to scale when the team knows whether its next limit is CPU, storage, connections, lock contention, network bandwidth, or human operational capacity.

> **Design check:** Which real operation benefits from your proposed partition key, and which one becomes more expensive because of it?

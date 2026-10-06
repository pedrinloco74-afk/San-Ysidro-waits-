# Practice the failure

## Design for the ordinary bad day

Operations are not a phase that begins after architecture. A data system is defined partly by how it behaves when a database is slow, a worker is stuck, a disk fills, a certificate expires, or a deployment has to be rolled back. These are not exotic exceptions; they are normal conditions that a dependable product learns to survive.

For each critical dependency, write a short failure note:

- What symptom will a customer notice?
- What should continue to work, and what should stop?
- Which metric or alert reveals the problem?
- What is the first safe mitigation?
- What state might need repair after recovery?

A dependency map is useful only if people can use it under pressure. Include owners, dashboards, runbooks, and the boundary of each service's responsibility. When an alert fires, it should point to a user impact or a concrete risk, not merely report that a graph crossed an unexplained line.

## Observe behavior at the right level

Logs help answer what happened to one request. Metrics reveal trends and saturation. Traces show where a request spent time across components. Events and audit records explain important business transitions. These signals complement one another; no single one replaces the rest.

Give each request a correlation ID that follows it across services, while avoiding secrets or personal data in log fields. Record state transitions with stable entity IDs and actor context. Use structured fields rather than relying on text that changes during refactoring. Sample high-volume traces deliberately, but preserve enough detail for rare failures and slow requests.

Monitor not only resource health but promises: confirmation latency, cancellation completion, projection freshness, oldest queue age, recovery point, and failed reservation rate. Alert on sustained customer harm and on early warning indicators that leave time to act. Every alert should have an owner and a next step.

## Backups are plans, not files

A backup is useful only if it can be restored. Define a recovery point objective—the maximum amount of recent data the business can afford to lose—and a recovery time objective—the longest acceptable time to restore service. Measure both in exercises. A backup that has never been restored is an assumption.

Practice restoring into an isolated environment. Verify record counts, checksums, key relationships, and application compatibility. Test the sequence for restoring encryption keys and credentials as well as data. A backup can be intact and unusable if its format, keys, or schema have changed without a tested path back.

For projections and caches, decide whether to rebuild from the authoritative source or restore a snapshot and replay changes. For event histories, validate retention and replay throughput. A recovery plan should explain which views will be temporarily stale and when they become trustworthy again.

## Deploy changes with an exit path

A safe deployment is not one that can never fail; it is one that detects failure early and has a bounded rollback or forward-fix path. Use small changes, gradual rollout, health checks tied to the promised behavior, and a clear decision threshold. Feature flags can separate shipping code from enabling behavior, but each flag needs an owner and removal date.

Data migrations need special care because reverting code does not reverse durable writes. Expand-and-contract changes, restartable backfills, and compatibility windows let old and new versions coexist. Before a risky change, record the current state, expected signals, rollback trigger, and who can approve it. Afterward, verify the result rather than inferring success from a green deployment job.

## Learn from incidents without blame

An incident review should reconstruct the conditions that made the failure possible, not search for one person to blame. Ask which assumptions were invisible, what signals were missing, why existing defenses did not contain the impact, and how the recovery could become easier. Then select a small number of changes with owners and dates.

The goal is not to prevent every error. It is to reduce the chance that one error becomes a broad outage, shorten the time to understand what is happening, and make recovery safe. Reliability grows through repeated practice: tabletop exercises, fault injection in controlled environments, restore drills, and post-deployment checks.

A mature system makes important failures boring. Operators can see the scope, customers receive an honest status, retries do not create duplicate effects, and restored data can be verified. The best emergency procedure is one the team has already rehearsed when there was no emergency.

> **Design check:** When was the last time the team restored a backup and proved the application could use it?

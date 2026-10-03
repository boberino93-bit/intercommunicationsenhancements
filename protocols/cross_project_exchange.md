# Cross-Project Exchange Protocol

Cross-project traffic is denied on the ordinary internal bus. Sharing requires a distinct exchange envelope naming source and destination projects, purpose, classification, requested artifacts, allowed use, expiry, correlation, and approval.

Data should be exported by value as the smallest useful sanitized snapshot. Imported data retains provenance. Trust is non-transitive.

## Default policy

`DENY`

A permitted exchange requires all of the following:

1. Explicit source and destination project IDs.
2. A caller with `CROSS_PROJECT_EXCHANGE` capability.
3. An approved exchange record.
4. A bounded purpose and allowed-use declaration.
5. Explicit artifact references rather than implicit context sharing.
6. Expiry where the exchange is time-sensitive.
7. Audit/provenance records on export and import.

Ordinary project channels never become cross-project channels merely because an agent can name another project.

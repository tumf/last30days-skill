## ADDED Requirements

### Requirement: X searches can run through xcom-rs CLI

The system SHALL support an `xcom_rs` backend that retrieves X search results by executing the `xcom-rs` CLI in non-interactive JSON mode, without adding direct X API HTTP calls to the Python application code.

#### Scenario: Primary X subquery uses xcom-rs
- GIVEN X is selected as a source and the resolved X backend is `xcom_rs`
- WHEN the pipeline executes a primary X search subquery
- THEN it uses the `xcom-rs` CLI adapter to execute the search
- AND it returns normalized X items in the shape expected by downstream ranking and clustering logic

#### Scenario: xcom-rs execution preserves date-bounded query intent
- GIVEN the planner emits an X search query with a requested time window
- WHEN the adapter constructs the CLI search request
- THEN the query includes the intended date constraints
- AND the adapter applies result limits based on the requested research depth

### Requirement: Supplemental X handle search uses the resolved CLI backend

The system SHALL support supplemental X handle search through the resolved CLI-backed X adapter using targeted `from:<handle>` query composition.

#### Scenario: Primary handle enrichment uses targeted search
- GIVEN the pipeline has extracted or received one or more X handles for supplemental enrichment
- WHEN the resolved X backend is `xcom_rs`
- THEN the pipeline performs targeted `from:<handle>` searches through the adapter
- AND it deduplicates resulting items against previously collected X URLs before adding them to the bundle

#### Scenario: Related handle results remain lower-priority evidence
- GIVEN both primary handles and related handles are available for supplemental search
- WHEN related handle results are returned through `xcom-rs`
- THEN they are added using a lower-priority supplemental label
- AND they remain distinguishable from primary-handle X evidence in fusion inputs

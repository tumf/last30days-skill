## ADDED Requirements

### Requirement: X search can run through xcom-rs CLI

The system MUST support an `xcom_rs` X backend that retrieves X search results by executing the `xcom-rs` CLI in non-interactive JSON mode, without adding direct X API HTTP calls to the Python application code.

#### Scenario: Primary X subquery uses xcom-rs

**Given** X is selected as a source and the resolved X backend is `xcom_rs`
**When** the pipeline executes a primary X search subquery
**Then** it uses the `xcom-rs` CLI adapter to execute the search
**And** it returns normalized X items in the same shape expected by downstream ranking and clustering logic

#### Scenario: xcom-rs execution preserves date-bounded query intent

**Given** the planner emits an X search query with a requested time window
**When** the adapter constructs the CLI search request
**Then** the search query includes the intended date constraints
**And** the adapter applies result limits based on the requested research depth

### Requirement: Supplemental handle search works with xcom-rs

The system MUST support supplemental X handle search through the same `xcom-rs` backend using targeted `from:<handle>` query composition.

#### Scenario: Primary handle enrichment uses targeted search

**Given** the pipeline has extracted or received one or more X handles for supplemental enrichment
**When** the resolved X backend is `xcom_rs`
**Then** the pipeline performs targeted `from:<handle>` searches through the adapter
**And** deduplicates resulting items against previously collected X URLs before adding them to the bundle

#### Scenario: Related handle results remain lower-priority evidence

**Given** both primary handles and related handles are available for supplemental search
**When** related handle results are returned through `xcom-rs`
**Then** they are added using a lower-priority supplemental label
**And** they remain distinguishable from primary-handle X evidence in fusion inputs

## MODIFIED Requirements

### Requirement: X backend resolution is explicit and diagnosable

The system MUST resolve X backend availability with explicit precedence rules and expose enough status metadata for diagnostics and operator guidance.

#### Scenario: xcom-rs is preferred when configured and available

**Given** local prerequisites for `xcom-rs` are available
**And** the operator explicitly selects `xcom_rs` or leaves backend choice on the preferred automatic path
**When** runtime provider selection is computed
**Then** the resolved X backend is `xcom_rs`
**And** runtime metadata reports that selection to diagnostic and reporting surfaces

#### Scenario: Diagnostics explain missing xcom-rs prerequisites

**Given** X retrieval is unavailable because `xcom-rs` prerequisites are missing
**When** the diagnostic banner or source-status output is rendered
**Then** the output explains which prerequisite is missing
**And** the guidance refers to `xcom-rs` setup rather than Bird cookies as the primary remediation path

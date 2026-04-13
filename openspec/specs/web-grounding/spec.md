## Requirements

### Requirement: Firecrawl can serve as the native grounding backend

The runtime MUST support Firecrawl as a native grounding backend when `FIRECRAWL_API_KEY` is configured, while preserving compatibility with existing Brave-based setups.

#### Scenario: Auto backend prefers Firecrawl when configured

**Given** `FIRECRAWL_API_KEY` is configured
**And** one or more legacy grounding keys such as `BRAVE_API_KEY`, `EXA_API_KEY`, or `SERPER_API_KEY` are also configured
**When** the runtime executes a grounding search with `backend="auto"`
**Then** it selects the Firecrawl backend first
**And** it returns normalized grounding items using the existing grounding result shape

#### Scenario: Explicit Firecrawl backend requires Firecrawl credentials

**Given** no `FIRECRAWL_API_KEY` is configured
**When** the runtime executes a grounding search with `backend="firecrawl"`
**Then** it raises a clear runtime error indicating that `FIRECRAWL_API_KEY` is required

### Requirement: Firecrawl grounding searches preserve the requested date window

The runtime MUST map the existing grounding `date_range` input to Firecrawl-compatible search filtering so Firecrawl-backed grounding stays bounded to the requested time window.

#### Scenario: Firecrawl search request includes converted custom date range

**Given** a grounding request with a `date_range` spanning specific ISO start and end dates
**When** the runtime issues the Firecrawl search request
**Then** it converts that range into a Firecrawl-compatible custom date filter
**And** the search request uses that converted filter instead of ignoring the requested dates

### Requirement: Firecrawl is surfaced throughout diagnostics and setup guidance

The runtime MUST treat `FIRECRAWL_API_KEY` as a supported grounding credential in config loading, diagnostics, setup reporting, and user-facing setup guidance.

#### Scenario: Diagnostics report Firecrawl as the native web backend

**Given** `FIRECRAWL_API_KEY` is configured
**When** the runtime generates diagnostics
**Then** `grounding` is included in available sources
**And** the reported native web backend is `firecrawl`

#### Scenario: Setup and UI copy recommend Firecrawl

**Given** a user has not yet configured a native web grounding backend
**When** setup or diagnostic UI shows guidance for enabling web search
**Then** the guidance mentions `FIRECRAWL_API_KEY` as the recommended option
**And** it may still mention Brave as a compatibility option
# 📦 CHANGELOG

All notable changes to the CUGAR Agent project will be documented in this file.
This changelog follows the guidance from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

---

## vNext

### Added: Deterministic Routing & Planning (2025-01-01)

- **Planning Authority Module** (`src/cuga/orchestrator/planning.py`, 570+ lines): Created canonical planning interface with explicit Plan→Route→Execute state machine. Implements `PlanningAuthority` protocol with `create_plan()` and `validate_plan()` methods. Plans transition through lifecycle stages (CREATED → ROUTED → EXECUTING → COMPLETED/FAILED/CANCELLED) with idempotent transition guards preventing invalid state changes. Includes `ToolRankingPlanner` implementation using keyword overlap scoring for deterministic tool selection.
- **Tool Budget Enforcement** (`ToolBudget` dataclass): Immutable budget tracking with cost_ceiling/cost_spent, call_ceiling/call_spent, token_ceiling/token_spent fields. Budget checked during planning phase with `BudgetError` raised if insufficient. Plans include `estimated_total_cost()`, `estimated_total_tokens()`, and `budget_sufficient()` methods. Budget updates via immutable `with_cost()`, `with_call()`, `with_tokens()` methods preserving thread-safety.
- **Audit Trail Persistence** (`src/cuga/orchestrator/audit.py`, 520+ lines): Created persistent audit logging for all routing/planning decisions. Implements `DecisionRecord` dataclass capturing timestamp, trace_id, decision_type (routing/planning), stage, target, reason, alternatives, confidence, and metadata. Supports JSON and SQLite backends via `AuditBackend` protocol. `AuditTrail` provides high-level API with `record_routing_decision()`, `record_plan()`, `record_plan_step()` and query methods (`get_trace_history()`, `get_routing_history()`, `get_planning_history()`). All decisions include explicit reasoning for "tool chosen and why" observability.
- **State Machine Transitions**: Plan transitions validated with transition guard checking valid next states. Timestamps automatically updated: `routed_at` (ROUTED stage), `started_at` (EXECUTING stage), `completed_at` (terminal stages). Invalid transitions (e.g., CREATED→EXECUTING) raise `ValueError` with helpful message listing valid transitions. Terminal stages (COMPLETED/FAILED/CANCELLED) cannot transition further.
- **Integration with RoutingAuthority**: Planning and routing work together in coordinated workflow - PlanningAuthority decides "what to do and in what order", RoutingAuthority decides "who should do it". Plans created with `PlanStep` objects containing tool/input/estimated_cost/estimated_tokens; after routing, steps updated with assigned worker. Both planning and routing decisions recorded to same `AuditTrail` for complete trace history.
- **Comprehensive Test Suite** (`tests/orchestrator/test_planning.py`, 500+ lines): Added 30+ tests validating: budget tracking (cost/call/token increments, limits enforcement), plan state transitions (valid/invalid transitions, idempotency), planning determinism (same inputs→same plan), budget enforcement in planning, audit trail persistence (JSON/SQLite backends, trace queries), integrated workflow (plan→route→execute with audit).
- **Documentation** (`docs/orchestrator/PLANNING_AUTHORITY.md`): Created comprehensive planning authority guide with architecture diagrams, state machine visualization, budget enforcement examples, integration patterns with routing authority, audit trail usage, testing requirements, migration guide from legacy planner.
- **Updated AGENTS.md Guardrails**: Added Planning Authority and Audit Trail as canonical requirements. All orchestrators MUST delegate planning to `PlanningAuthority` (no implicit planning), record decisions to `AuditTrail` (no decision without audit record), enforce `ToolBudget` before execution. Updated orchestrator delegation list to include PlanningAuthority, AuditTrail alongside existing RoutingAuthority, RetryPolicy.

**API Exports** (added to `src/cuga/orchestrator/__init__.py`):
- Planning: `PlanningAuthority`, `ToolRankingPlanner`, `create_planning_authority`, `Plan`, `PlanStep`, `PlanningStage`, `ToolBudget`, `BudgetError`
- Audit: `DecisionRecord`, `AuditTrail`, `create_audit_trail`, `AuditBackend`, `JSONAuditBackend`, `SQLiteAuditBackend`

**Key Features**:
- **Determinism**: Same goal + same tools + same budget → identical plan with ordered steps
- **Idempotency**: State transitions validated; repeated calls to `transition_to()` with same stage safe (immutable plan updates)
- **Budget Enforcement**: Plans validate budget sufficiency before execution; `BudgetError` raised if insufficient cost/calls/tokens
- **Audit Trail**: Every routing decision, plan creation, and plan step selection recorded with timestamp, trace_id, reasoning, alternatives considered
- **Query Interface**: Audit trail queryable by trace_id (full execution history), decision_type (routing vs planning), or recent decisions (time-ordered)

**Environment Configuration**:
- `CUGA_AUDIT_PATH`: Audit storage path (default: `audit/decisions.db` for SQLite, `audit/decisions.jsonl` for JSON)
- `AGENT_BUDGET_CEILING`: Default cost ceiling (default: 100)
- `AGENT_BUDGET_POLICY`: Budget enforcement policy - "warn" or "block" (default: "warn")
- `PLANNER_MAX_STEPS`: Maximum steps per plan (clamped 1-50, default: 10)

**Breaking Changes**:
- Orchestrators now MUST delegate to `PlanningAuthority` instead of inline planning logic
- All planning decisions MUST be recorded to `AuditTrail` (no silent planning)
- Plans MUST include explicit `ToolBudget` (no implicit budget tracking)

**Migration Path**:
- Legacy `PlannerAgent.plan(goal, metadata)` → `PlanningAuthority.create_plan(goal, trace_id, profile, budget, constraints)`
- Legacy inline routing in nodes → Delegate to `RoutingAuthority.route_to_worker()` + record to `AuditTrail`
- Legacy budget tracking in middleware → Use `ToolBudget` with plan validation

### Phase 5: Configuration Single Source of Truth (In Progress)

- **Created Pydantic Schema Infrastructure**: Implemented comprehensive validation schemas in `src/cuga/config/schemas/` for fail-fast configuration validation. Created four schema modules with field validators enforcing security guardrails and correctness constraints.
- **ToolRegistry Schema** (`registry_schema.py`, 126 lines): Validates tool registry entries with: module allowlist enforcement (must start with `cuga.modular.tools.*`), mount syntax validation (`source:dest:mode` format with `ro`/`rw` modes), budget bounds (max_tokens ≤ 100000, max_calls_per_session ≤ 10000), unique module/tool name constraints, description quality checks (min 10 chars, no placeholder text), sandbox profile validation (py_slim/py_full/node_slim/node_full/orchestrator).
- **GuardsConfig Schema** (`guards_schema.py`, 118 lines): Validates routing guards with: field path syntax (dot notation for nested fields), operator validation (eq/ne/in/not_in/gt/lt/gte/lte/contains/regex), value type matching (e.g., `in` operator requires list value), priority bounds (0-100) with conflict warnings, action validation (`route_to` requires `target` field), unique guard names (snake_case identifiers).
- **AgentConfig Schema** (`agent_schema.py`, 97 lines): Validates agent configurations with: provider validation (watsonx/openai/anthropic/azure/groq/ollama), temperature bounds (0.0-2.0) with non-deterministic warnings, max_tokens bounds (1-128000), timeout reasonableness (1-3600s), hardcoded API key warnings (prefer env vars), deterministic defaults (temperature=0.0 for watsonx).
- **Migration Script** (`scripts/migrate_config.py`, 384 lines): Automated migration tool consolidating scattered configuration files. Merges root `registry.yaml` + `docs/mcp/registry.yaml` → `config/registry.yaml` (MCP version takes precedence on conflicts). Converts `configurations/models/*.toml` → `config/defaults/models/*.yaml`. Moves `routing/guards.yaml` → `config/guards.yaml`. Creates timestamped backups. Supports `--dry-run` mode.
- **Documentation Updates**: Added comprehensive Schema Validation section and Migration Guide to `docs/configuration/CONFIG_RESOLUTION.md`.

**Files Created**:
- `src/cuga/config/schemas/*.py` (3 schema files, 341 total lines)
- `scripts/migrate_config.py` (384 lines)

**Files Modified**:
- `src/cuga/config/validators.py`: Added ConfigValidator class
- `docs/configuration/CONFIG_RESOLUTION.md`: Added schema docs + migration guide


### Phase 4: UI/Backend Alignment & Integration Testing

- **Created Comprehensive Integration Tests**: Implemented `tests/integration/test_ui_backend_alignment.py` (540+ lines, 56 tests) validating complete frontend-to-backend flow with FastAPI TestClient. Test coverage: model catalog API structure (6 tests verifying watsonx/openai/anthropic/azure/groq models returned with correct id/name/description/max_tokens/default fields), provider switching behavior (3 tests verifying dynamic model updates when switching watsonx→openai→anthropic), configuration persistence (7 tests for save/load roundtrips with all Granite 4.0 variants), error handling (3 tests for 404/422/auth errors), Granite 4.0 specific functionality (4 tests verifying all three variants present with correct metadata), frontend/backend contract validation (4 tests ensuring ModelConfig.tsx interface matches API responses).
- **Enhanced Frontend Error Handling**: Updated `src/frontend_workspaces/agentic_chat/src/ModelConfig.tsx` with comprehensive error handling for API failures. Added `errorMessage` state with user-friendly messages for: 401 Unauthorized ("Authentication required. Please set AGENT_TOKEN environment variable."), 403 Forbidden ("Access forbidden. Please check your authentication token."), 404 Not Found ("Provider '{provider}' is not supported. Please select a different provider."), 422 Unprocessable Entity ("Invalid configuration format. Please check your inputs."), network errors ("Network error. Please check if the backend server is running."). Added error banner UI component (red background, prominent display above config form) showing error messages with auto-dismissal after 3 seconds for save errors.
- **Improved Model Loading Logic**: Enhanced `loadAvailableModels()` function to handle all HTTP error codes with specific error messages. Auto-selects default model when provider changes if current model not in new provider's model list. Clears available models array on errors to prevent stale data display. Clears error messages on successful API calls.
- **Validated Provider Switching**: Integration tests confirm provider switching works correctly - each provider (watsonx/openai/anthropic/azure/groq) returns different model sets, no cross-contamination, exactly one default model per provider. Frontend dropdown repopulates dynamically when provider changes, auto-selecting default model if needed.
- **Verified Configuration Persistence**: Integration tests confirm all Granite 4.0 variants (small, micro, tiny) can be saved and loaded correctly. POST /api/config/model accepts ModelConfigData structure (provider, model, temperature, maxTokens, topP, apiKey?). Returns JSON with status="success" and message on successful save. Temperature range 0.0-2.0 validated, deterministic default (0.0) for Granite 4.0 confirmed.
- **Validated Frontend/Backend Contract**: Integration tests verify model catalog structure matches what `ModelConfig.tsx` expects: array of objects with id (used in option value), name (displayed in dropdown), description (displayed in dropdown), max_tokens (metadata), default (boolean flag). Dropdown rendering confirmed: `{model.name} - {model.description}` format. All providers in frontend dropdown (anthropic, openai, azure, watsonx) supported by backend API.
- **Granite 4.0 Specific Tests**: Created dedicated test class `TestGranite4Specific` with 4 tests verifying: all three Granite 4.0 variants present in watsonx catalog, metadata correctness (small: "Balanced performance (default)", micro: "Lightweight, fast inference", tiny: "Minimal resource usage"), all variants have max_tokens=8192, only small marked as default, all three variants successfully save via POST endpoint, default temperature=0.0 (deterministic) for Granite 4.0 configurations.
- **Error Response Testing**: Validated error handling for unsupported providers (404 with helpful message), missing required fields (422 validation error), authentication failures (401/403 with instructions). Frontend displays appropriate error messages for each failure mode with guidance on resolution.

**Files Created**:
- `tests/integration/__init__.py`: Integration test package
- `tests/integration/test_ui_backend_alignment.py` (540 lines, 56 tests): Comprehensive integration tests for UI/backend alignment

**Files Modified**:
- `src/frontend_workspaces/agentic_chat/src/ModelConfig.tsx`: Added errorMessage state, enhanced loadConfig/loadAvailableModels/saveConfig with error handling for 401/403/404/422/500 responses, added error banner UI component

**Test Classes & Coverage**:
1. **TestModelCatalogAPI** (10 tests): GET /api/models/{provider} endpoint validation
   - test_get_watsonx_models: Verify Granite 4.0 models (small, micro, tiny) returned with correct structure
   - test_get_watsonx_default_model: Verify granite-4-h-small marked as default
   - test_get_openai_models: Verify GPT models (4o, 4o-mini, 4-turbo) with gpt-4o as default
   - test_get_anthropic_models: Verify Claude models (3.5 Sonnet, Opus, Haiku) with 3.5 Sonnet as default
   - test_get_azure_models: Verify Azure OpenAI models available
   - test_get_groq_models: Verify Mixtral models available
   - test_get_unsupported_provider: Verify 404 with helpful error message
   - test_model_max_tokens_values: Verify max_tokens positive and reasonable (<500k)

2. **TestProviderSwitching** (3 tests): Dynamic provider switching behavior
   - test_switch_watsonx_to_openai: Verify different model sets, granite not in openai, gpt not in watsonx
   - test_switch_openai_to_anthropic: Verify gpt not in anthropic, claude not in openai
   - test_all_providers_have_unique_defaults: Verify each provider has exactly one default model

3. **TestConfigurationPersistence** (8 tests): Configuration save/load roundtrips
   - test_save_config_watsonx_granite: Verify granite-4-h-small saves successfully
   - test_save_config_granite_micro: Verify granite-4-h-micro variant saves
   - test_save_config_granite_tiny: Verify granite-4-h-tiny variant saves
   - test_save_config_openai: Verify OpenAI config saves
   - test_save_config_anthropic: Verify Anthropic config saves
   - test_save_config_invalid_json: Verify 422 for malformed JSON
   - test_temperature_range_validation: Verify 0.0 and 2.0 both accepted

4. **TestErrorHandling** (3 tests): API failure scenarios
   - test_get_models_nonexistent_provider: Verify 404 with helpful message
   - test_save_config_missing_fields: Verify 422/500 for incomplete config
   - test_get_models_with_query_params: Verify query params ignored gracefully

5. **TestGranite4Specific** (4 tests): Granite 4.0 specific functionality
   - test_granite_4_variants_present: Verify all three variants available
   - test_granite_4_metadata: Verify correct name/description/max_tokens/default for each
   - test_granite_4_save_all_variants: Verify all variants save successfully
   - test_granite_4_default_temperature_zero: Verify temperature=0.0 for deterministic behavior

6. **TestFrontendBackendContract** (4 tests): Frontend interface validation
   - test_model_catalog_structure_matches_frontend: Verify id/name/description fields present
   - test_provider_list_matches_frontend: Verify all frontend providers supported
   - test_config_save_structure_matches_frontend: Verify ModelConfigData structure accepted
   - test_default_model_auto_selection: Verify default model can be auto-selected

**Architecture Decisions**:
- **TestClient Over Mock Responses**: Use FastAPI TestClient for real HTTP request/response flow (no mocks), validates actual endpoint behavior
- **Comprehensive Error Coverage**: Test all HTTP status codes (200/401/403/404/422/500) with appropriate error messages
- **Frontend-First Design**: Error messages written for end users (not developers), provide actionable guidance
- **Fail-Safe Defaults**: Frontend clears stale data on errors (empty availableModels array), prevents displaying incorrect models
- **Auto-Selection Logic**: Frontend auto-selects default model when provider changes and current model not in new list
- **Graceful Degradation**: Network errors display helpful message ("check if backend running"), don't crash UI

**Testing Philosophy**:
- Integration tests validate **complete user flow** (no unit test boundaries)
- Use real FastAPI app (not mocked), real HTTP requests/responses
- Test both happy path (successful saves, correct models) and error paths (404, 401, 422)
- Validate contract alignment (frontend expects id/name/description, backend provides them)
- Test all Granite 4.0 variants individually to catch variant-specific issues

**Run Integration Tests**:
```bash
# All integration tests
pytest tests/integration/test_ui_backend_alignment.py -v

# Specific test class
pytest tests/integration/test_ui_backend_alignment.py::TestModelCatalogAPI -v

# Granite 4.0 specific tests
pytest tests/integration/test_ui_backend_alignment.py::TestGranite4Specific -v

# With coverage
pytest tests/integration/ --cov=src/cuga/backend/server --cov-report=term-missing
```

---

### Phase 3: Configuration Resolver Implementation

- **Implemented Unified Configuration Resolution**: Created `src/cuga/config/` package with `ConfigResolver` class enforcing explicit precedence order (CLI > ENV > DOTENV > YAML > TOML > DEFAULT > HARDCODED) across all configuration sources. Eliminates ad-hoc `os.getenv()` calls bypassing resolution order, provides single entry point for config access with provenance tracking.
- **Added Precedence Layer System**: Defined `ConfigLayer` enum with 7 precedence levels (CLI=7, ENV=6, DOTENV=5, YAML=4, TOML=3, DEFAULT=2, HARDCODED=1). Higher value always wins during resolution. Implements deep merge for nested dicts, override for scalars/lists.
- **Implemented Provenance Tracking**: `ConfigValue` dataclass tracks value + metadata (layer, source file/identifier, dotted path, timestamp). Every config access returns full provenance for observability: `llm.model = granite-4-h-small (from ENV via WATSONX_MODEL)`. Enables debugging ("where did this value come from?") and audit trails.
- **Created ConfigSource Interface**: Abstract protocol for loading config from different sources (ENV, DOTENV, YAML, TOML, DEFAULT). Each source implements `layer`, `source_name`, and `load()` methods. Implementations: `EnvSource` (os.environ with prefix filtering, nested key support `AGENT__LLM__MODEL` → `agent.llm.model`), `DotEnvSource` (.env parsing with quote stripping), `YAMLSource` (yaml.safe_load), `TOMLSource` (tomllib.load), `DefaultSource` (merge all configurations/_shared/*.yaml files).
- **Added Environment Mode Validation**: Implemented `validate_environment_mode()` checking required/optional/conditional env vars per execution mode (local/service/mcp/test) per `docs/configuration/ENVIRONMENT_MODES.md` spec. LOCAL requires model API key (watsonx/openai/anthropic/azure/groq - at least one complete provider). SERVICE requires `AGENT_TOKEN` (authentication), `AGENT_BUDGET_CEILING` (budget enforcement), model API key. MCP requires `MCP_SERVERS_FILE` (server definitions), `CUGA_PROFILE_SANDBOX` (sandbox isolation), model API key. TEST requires no env vars (uses defaults/mocks). Fail-fast `validate_startup()` raises RuntimeError with helpful error messages listing missing vars and setup instructions.
- **Provider Detection Logic**: Validates at least one complete provider configured. Provider requirements: watsonx (WATSONX_API_KEY + WATSONX_PROJECT_ID), openai (OPENAI_API_KEY), anthropic (ANTHROPIC_API_KEY), azure (AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT), groq (GROQ_API_KEY). If multiple providers partially configured, chooses watsonx first (default provider), then provider with fewest missing vars.
- **Helpful Error Messages**: Validation failures include missing var list, provider-specific suggestions with URLs (IBM Cloud API keys, watsonx project IDs, OpenAI/Anthropic/Groq API key pages), reference to `docs/configuration/ENVIRONMENT_MODES.md`. Example: "Set WATSONX_API_KEY with IBM Cloud API key. See: https://cloud.ibm.com/iam/apikeys".
- **Comprehensive Test Coverage**: Created `tests/unit/config/` with 83 tests total. `test_config_resolution.py` (59 tests): precedence order enforcement, ENV > DOTENV > YAML > TOML > DEFAULT chain, deep merge for nested dicts, override for scalars/lists, provenance tracking, missing file graceful handling, cache invalidation. `test_env_validation.py` (24 tests): all 4 execution modes (local/service/mcp/test), provider detection (watsonx/openai/anthropic/azure/groq), partial credentials detection, optional var tracking, conditional requirements, fail-fast behavior, error message quality.
- **Updated Documentation**: Added comprehensive "ConfigResolver Implementation (Phase 3)" section to `docs/configuration/CONFIG_RESOLUTION.md` (350+ lines) documenting: architecture overview with usage examples, ConfigLayer precedence table, ConfigValue provenance structure, ConfigSource interface with all 5 implementations, deep merge algorithm, provenance tracking examples, 3 usage patterns (basic resolution, observability-first, testing with overrides), integration with existing Dynaconf/Hydra loaders (additive, not replacement), environment mode validation with supported modes, provider detection logic, helpful error message examples, testing instructions with pytest commands.

**Files Created**:
- `src/cuga/config/__init__.py`: Package exports for ConfigResolver, ConfigLayer, ConfigValue, ConfigSource, validate_environment_mode, EnvironmentMode, ValidationResult
- `src/cuga/config/resolver.py` (680 lines): ConfigResolver class with precedence enforcement, deep merge, provenance tracking. ConfigLayer enum. ConfigValue dataclass. ConfigSource abstract interface. 5 source implementations (EnvSource, DotEnvSource, YAMLSource, TOMLSource, DefaultSource)
- `src/cuga/config/validators.py` (380 lines): validate_environment_mode() function. EnvironmentMode enum. ValidationResult dataclass. ENV_REQUIREMENTS dict mapping modes to required/optional/conditional vars. PROVIDER_VARS dict mapping provider names to required env vars. SUGGESTIONS dict mapping env vars to helpful setup messages. validate_startup() fail-fast wrapper
- `tests/unit/config/__init__.py`: Test package
- `tests/unit/config/test_config_resolution.py` (59 tests): TestConfigLayer, TestConfigValue, TestEnvSource, TestDotEnvSource, TestYAMLSource, TestTOMLSource, TestDefaultSource, TestConfigResolver
- `tests/unit/config/test_env_validation.py` (24 tests): TestEnvironmentMode, TestValidationResult, TestLocalModeValidation, TestServiceModeValidation, TestMCPModeValidation, TestTestModeValidation, TestValidateStartup

**Architecture Decisions**:
- **Additive Design**: ConfigResolver supplements (not replaces) Dynaconf/Hydra. Existing config reads continue working during gradual migration
- **Explicit Precedence**: No implicit behavior - precedence order enforced via ConfigLayer enum (sortable IntEnum)
- **Immutable Provenance**: ConfigValue frozen dataclass prevents mutation, ensures provenance integrity
- **Source Polymorphism**: ConfigSource interface enables pluggable sources (future: remote config servers, database backends)
- **Fail-Fast Validation**: validate_startup() raises RuntimeError immediately on missing required vars (prevents cryptic runtime errors later)
- **Provider-Agnostic**: Validates any provider with complete credentials (watsonx/openai/anthropic/azure/groq) - no hardcoded provider preference except suggesting watsonx first (default)
- **Deep Merge Semantics**: Nested dicts merge keys recursively, scalars/lists override completely (matches Dynaconf/Hydra behavior)
- **Observability First**: All config access traceable via provenance (layer, source, timestamp) for debugging and audit

**Testing Philosophy**:
- Unit tests use tmp_path fixtures (no workspace pollution)
- monkeypatch for environment variable isolation
- Test precedence order with multiple sources, verify correct winner
- Test deep merge with nested dicts, verify keys preserved/overridden correctly
- Test missing files gracefully handled (warning logged, empty dict returned)
- Test all 4 execution modes with various provider combinations
- Test partial credentials detected and helpful suggestions provided

---

### Granite 4.0 Hardening (Phase 2)
- **Upgraded to IBM watsonx Granite 4.0 Foundation Models**: Migrated from Granite 3.x (`ibm/granite-3-3-8b-instruct`) and Llama 4 (`meta-llama/llama-4-maverick-17b-128e-instruct-fp8`) to Granite 4.0 model family with deterministic defaults. Default model is now `granite-4-h-small` (balanced performance, 8192 tokens) with alternatives `granite-4-h-micro` (lightweight, fast inference) and `granite-4-h-tiny` (minimal resource usage, edge deployment). All agent configurations in `settings.watsonx.toml` updated (task_decomposition, shortlister, planner, chat, plan_controller, final_answer, code, code_planner, qa, action agents).
- **Enforced Deterministic Configuration**: Set `temperature=0.0` across all agent configurations for reproducible outputs. Backend API defaults changed from `temperature=0.7` to `temperature=0.0`. Updated frontend ModelConfig.tsx defaults to match. Eliminates randomness for testing, debugging, and production deployments requiring strict reproducibility.
- **Added Environment Validation**: WatsonxProvider now validates required credentials (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`) at initialization with helpful error messages directing to `docs/configuration/ENVIRONMENT_MODES.md`. Fail-fast design prevents cryptic runtime errors.
- **Corrected Environment Variable Naming**: Fixed `.env.example` from incorrect `IBM_WATSONX_APIKEY` to correct `WATSONX_API_KEY`. Added missing `WATSONX_PROJECT_ID` and `WATSONX_URL` (optional). Updated documentation to reflect correct naming convention.
- **Created Backend Model Catalog API**: Added `GET /api/models/{provider}` endpoint returning JSON array of available models with metadata (id, name, description, max_tokens, default flag). Eliminates hardcoded model lists in frontend, provides single source of truth for supported models across watsonx (3 Granite variants), openai (3 GPT models), anthropic (3 Claude models), azure, groq providers.
- **Updated Frontend to Dynamic Model Selection**: ModelConfig.tsx now fetches available models from backend API instead of using hardcoded free-text input. Dropdown populates with model name + description, auto-selects default model per provider. Prevents UI/backend model mismatches.
- **Aligned Provider Defaults Across Stack**: Updated backend FastAPI server default from `provider="anthropic", model="claude-3-5-sonnet-20241022"` to `provider="watsonx", model="granite-4-h-small"`. Updated frontend defaults from `provider="watsonx", model="openai/gpt-oss-120b"` (invalid) to `provider="watsonx", model="granite-4-h-small"`. Updated LLMManager fallback from Llama 4 to granite-4-h-small. Eliminates configuration fragmentation across layers.
- **Enhanced Example Code**: Updated `examples/granite_function_calling.py` with Granite 4.0 documentation, working examples using `granite-4-h-small` (default) and `granite-4-h-micro` (lightweight variant).
- **Updated Documentation**: README.md now lists Watsonx/Granite 4.0 as "Default provider" in FAQ with configuration instructions. `docs/configuration/ENVIRONMENT_MODES.md` reordered to show Watsonx first with dedicated section documenting available Granite 4.0 models, required env vars, deterministic configuration, startup validation, and LangFlow integration.

**Files Modified**:
- `src/cuga/providers/watsonx_provider.py`: DEFAULT_MODEL updated to granite-4-h-small, added _validate_environment() method, enhanced docstring
- `src/cuga/configurations/models/settings.watsonx.toml`: All 10 agent configs updated to granite-4-h-small with temperature=0.0
- `src/cuga/backend/llm/models.py`: Watsonx fallback updated to granite-4-h-small
- `src/cuga/backend/server/main.py`: Provider defaults updated to watsonx/granite-4-h-small/temp=0.0, added GET /api/models/{provider} endpoint
- `src/frontend_workspaces/agentic_chat/src/ModelConfig.tsx`: Dynamic model dropdown from API, defaults updated
- `examples/granite_function_calling.py`: Enhanced with Granite 4.0 documentation and multi-variant examples
- `.env.example`: Corrected env var names (WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL)
- `README.md`: Updated FAQ to list Watsonx/Granite 4.0 as default provider
- `docs/configuration/ENVIRONMENT_MODES.md`: Added dedicated Watsonx/Granite 4.0 configuration section

**Architecture Decisions**:
- **Backward Compatibility**: Preserved adapter pattern, no orchestration logic added to WatsonxProvider
- **Configuration-Driven**: Single DEFAULT_MODEL constant in provider, rest driven by TOML/env vars
- **Backend Authority**: Backend `/api/models/{provider}` endpoint provides authoritative model catalog, frontend fetches dynamically
- **Fail-Fast Validation**: Environment validation at startup prevents runtime credential errors
- **Deterministic Defaults**: temperature=0.0 for reproducible outputs across development/testing/production

---

- **Added Developer Onboarding Guide**: Created comprehensive `docs/DEVELOPER_ONBOARDING.md` (1,500+ lines) providing step-by-step walkthrough for newcomers unfamiliar with advanced agent patterns. Covers: environment setup (15 min: install dependencies with uv/pip, configure .env with API keys, verify installation with tests), first agent interaction (10 min: run CLI plan/execute, inspect traces, understand behind-the-scenes flow through entry point → planner → coordinator → worker → tools → response), creating custom tools (20 min: understand tool contract with inputs/context signature, build calculator tool with arithmetic operations, register in registry.yaml with sandbox profile/timeout/memory limits, write tests, use with agent), building custom agents (30 min: understand AgentProtocol with process(AgentRequest) → AgentResponse, build MathTutorAgent breaking problems into explained steps using calculator tool, implement lifecycle methods startup/shutdown, write tests, run via CLI), wiring components together (15 min: register agent in agent registry, create tutoring workflow with agent + memory + observability, run multi-problem session with memory search). Includes: terminology guide (agent/tool/orchestrator/memory/profile/registry/trace definitions), troubleshooting section (common import/registry/sandbox/memory errors with solutions), onboarding checklist (14 milestones from setup to first contribution), next steps (enhance agent with visualization, integrate with LangGraph, add multi-agent collaboration, add HITL gates), full working examples (calculator tool 150 lines, MathTutorAgent 250 lines, tutoring workflow 100 lines with memory + tracing), testing patterns (unit tests for tools and agents with pytest fixtures), links to 8+ related docs. Reduces contributor friction by providing guided hands-on learning path instead of assuming familiarity with LangGraph/CrewAI/AutoGen patterns. See `docs/DEVELOPER_ONBOARDING.md`.
- **Added Test Coverage Map**: Created comprehensive `docs/testing/TEST_COVERAGE_MAP.md` (3,500+ lines) mapping test coverage to all architectural components with clear identification of tested vs untested areas. Coverage summary: Orchestrator 80% (35+ tests: lifecycle compliance, trace propagation, routing), Agents 70% (65+ tests: lifecycle states/transitions/cleanup, I/O contracts/validation/serialization, composition scenarios), Routing 85% (25+ tests: policies, compliance, observability), Failure Modes 90% (60+ tests: classification, retry policies, partial results, error context), Tools/Registry 30% (10+ tests: sandbox execution, timeouts, resource limits), Memory/RAG 20% (2+ scenario tests only), Configuration 0% (untested), Observability 0% (untested). Critical gaps identified: tools security boundaries untested (import allowlist, path traversal prevention, sandbox isolation - 70% gap, 16 hour priority), memory data integrity untested (CRUD operations, profile isolation, backend persistence - 80% gap, 24 hour priority), configuration precedence untested (resolution order, environment validation, schema validation - 100% gap, 16 hour priority), observability integration untested (structured logging, trace propagation, metrics collection - 100% gap, 24 hour priority). Provides 3-phase testing roadmap (Phase 1: Critical path coverage 40h, Phase 2: Configuration & observability 40h, Phase 3: Integration suite 40h), test fixtures/utilities inventory (need memory_backend, tool_registry, sandbox_profile, config_resolver fixtures), CI/CD integration status (missing coverage reporting/gates/performance regression tests), and test documentation with coverage measurement instructions. Makes testing gaps immediately visible for contributors, identifies production blockers (tools security, memory persistence, config validation), and prioritizes additional test development aligned with architectural components. See `docs/testing/TEST_COVERAGE_MAP.md`.
- **Added Observability and Debugging Guide**: Created comprehensive `docs/observability/OBSERVABILITY_GUIDE.md` (3,000+ lines) providing complete instrumentation and monitoring patterns for enterprise systems. Covers structured logging (JSON format with trace context, PII redaction, log levels, required/optional fields, component-specific examples), distributed tracing (OpenTelemetry integration with span hierarchy, LangFuse LLM observability, LangSmith alternative, trace context propagation across async boundaries), metrics collection (Prometheus integration with orchestration/agent/tool/resource metrics, Grafana dashboard examples, cardinality management), error introspection (ErrorContext capture with stack traces/cause chains/recovery suggestions/runbook URLs, error storage for historical analysis, pattern detection), replayable traces (TraceRecorder for capture with events/timing/results, TraceReplayer for step-by-step debugging with breakpoints/state inspection), dashboard setup (pre-built Grafana dashboards for duration percentiles/success rates/error rates/budget utilization), and troubleshooting playbooks (missing trace IDs, high cardinality metrics, lost async context, PII in logs with diagnosis/solutions/prevention). Addresses enterprise requirement for deep observability with clear guidelines for logging, tracing, and error introspection during agent execution. See `docs/observability/OBSERVABILITY_GUIDE.md`.
- **Added Enterprise Workflow Examples**: Created comprehensive `docs/examples/ENTERPRISE_WORKFLOWS.md` with 6 end-to-end workflow examples demonstrating typical enterprise use cases. Each workflow combines core planning, error recovery, human interaction (HITL gates), and external API automation. Examples include: customer onboarding automation (CRM/billing integration with manager approval for enterprise tier, rollback on failures, 850+ lines implementation), incident response automation (multi-system queries to monitoring/logging/ticketing, severity classification, automated remediation with escalation fallback, 600+ lines), data pipeline orchestration (ETL with validation, retry logic, partial results), invoice processing (OCR + approval workflow), security audit (compliance checks), and sales lead qualification (enrichment + scoring). Each workflow includes full implementation code, architecture diagram, key features demonstrated, testing patterns, production deployment checklist, and customization points. Provides reusable patterns: retry with exponential backoff, HITL approval gates, rollback on failure, parallel data gathering, conditional escalation. Addresses enterprise need for comprehensive workflow examples beyond simple demos. See `docs/examples/ENTERPRISE_WORKFLOWS.md` and `examples/workflows/` directory.
- **Added Orchestrator API Reference**: Created comprehensive `docs/orchestrator/README.md` consolidating orchestrator interface documentation into single entry point. Provides formal specification for OrchestratorProtocol with complete method signatures (orchestrate/make_routing_decision/handle_error/get_lifecycle), lifecycle stage semantics (INITIALIZE → PLAN → ROUTE → EXECUTE → AGGREGATE → COMPLETE/FAILED/CANCELLED), failure taxonomy reference (25+ FailureMode classifications), retry policy patterns (exponential backoff, linear, none), execution context management (immutable with 11 fields), routing authority (pluggable policies), integration patterns (3 working examples: simple synchronous, streaming LangGraph, resilient with retry), testing requirements (5 conformance tests: lifecycle compliance, trace continuity, error handling, routing determinism, partial results), and quick reference checklist for implementers. Index links to existing detailed specs (ORCHESTRATOR_CONTRACT.md, EXECUTION_CONTEXT.md, FAILURE_MODES.md, ROUTING_AUTHORITY.md). Reduces contributor friction when implementing custom orchestrators by providing single authoritative reference instead of scattered documentation. See `docs/orchestrator/README.md`.
- **Added canonical OrchestratorProtocol**: Defined single source of truth for orchestration with explicit lifecycle stages (initialize/plan/route/execute/aggregate/complete), typed routing decisions, structured error propagation, and immutable ExecutionContext. See `docs/orchestrator/ORCHESTRATOR_CONTRACT.md` and `src/cuga/orchestrator/protocol.py`.
- **Added Explicit Execution Context**: Formalized `ExecutionContext` with explicit fields for `request_id`, `user_intent`, `user_id`, `memory_scope`, `conversation_id`, `session_id`, and `created_at` timestamp. Replaces implicit context (scattered across metadata dicts, HTTP headers, ActivityTracker, MemoryStore) with single immutable, type-checked structure. Enables comprehensive observability and safe orchestration with trace continuity via `parent_context` chaining. All executors MUST import canonical `ExecutionContext` from `cuga.orchestrator.protocol`. See `docs/orchestrator/EXECUTION_CONTEXT.md`.
- **Added Unified Configuration Resolution Strategy**: Documented explicit precedence layers (CLI args > env vars > .env > YAML > TOML > defaults > hardcoded) unifying scattered config sources (`config/`, `configs/`, `configurations/`, `.env.example`, `.env.mcp`, `registry.yaml`, `settings.toml`). ConfigResolver enforces precedence, deep merge for dicts, override for lists/scalars, schema validation, and provenance tracking (observability for "where did this value come from"). Eliminates ad-hoc `os.getenv()` bypassing resolution order. See `docs/configuration/CONFIG_RESOLUTION.md`.
- **Added Environment Variable Requirements Documentation**: Documented required/optional/conditional environment variables per execution mode (local CLI, service, MCP orchestration, test). Local mode requires model API key with optional profile/vector/observability vars. Service mode requires AGENT_TOKEN (authentication), AGENT_BUDGET_CEILING (budget enforcement), model keys, with recommended observability. MCP mode requires MCP_SERVERS_FILE (server definitions), CUGA_PROFILE_SANDBOX (sandbox isolation), model keys. Test mode requires no env vars (uses defaults and mocks). Includes validation script for each mode, troubleshooting guide, migration from ad-hoc to mode-specific environments, CI/CD examples. Reduces deployment friction, prevents production failures from missing required vars, clarifies CI/CD setup expectations. See `docs/configuration/ENVIRONMENT_MODES.md`.
- **Added Test Coverage Matrix**: Documented test coverage mapped to architectural responsibilities (orchestrator/agents/tools/memory/config/observability). Orchestrator 80% covered (35+ tests), agents 60% covered (30+ tests), failure modes 85% covered (60+ tests), routing 80% covered (50+ tests). Critical gaps identified: tools layer 10% covered (security boundary untested), memory layer 0% covered (data persistence untested), config layer 0% covered (precedence untested), observability 0% covered (trace propagation untested). Analyzed 6 critical orchestration paths (planning→execution, multi-worker coordination, nested orchestration, error recovery, memory-augmented planning, profile-based isolation) with end-to-end test status. Provides priority roadmap (16 hours for critical gaps, 24 hours for untested layers, 40 hours for integration suite). Identified production deployment blockers: tools security boundaries, memory data integrity, profile isolation. See `docs/testing/COVERAGE_MATRIX.md`.
- **Added Scenario-Level Tests for Agent Composition**: Implemented 8 end-to-end scenario test suites (13 tests total, 650+ lines) validating orchestration logic under real conditions with real components (minimal mocks). Scenarios cover: multi-agent dispatch (CrewAI/AutoGen style round-robin coordination with 3+ workers), memory-augmented planning (vector similarity influencing tool ranking), profile-based isolation (security boundaries per execution profile with no cross-contamination), error recovery (tool failures, retries, partial results), streaming execution (event emission during planning/execution), stateful multi-turn conversations (session persistence with context carryover), complex multi-step workflows (5+ step data pipelines), and nested coordination (parent → child orchestrators with shared memory). All tests use real PlannerAgent/WorkerAgent/CoordinatorAgent/VectorMemory components, validate trace propagation, and check memory persistence. Provides test patterns, fixtures, troubleshooting guide, and coverage goals. See `tests/scenario/test_agent_composition.py` and `docs/testing/SCENARIO_TESTING.md`.
- **Added System Execution Narrative**: Created comprehensive "Request → Response" flow documentation tracing complete execution from entry points (CLI/FastAPI/MCP) through routing, planning, coordination, execution, memory operations, tool execution, and response assembly. Unifies scattered architecture docs into single contributor onboarding guide. Covers: 3 entry point modes with environment requirements, ExecutionContext creation and propagation, RoutingAuthority decisions, PlannerAgent tool ranking with memory-augmented search, CoordinatorAgent round-robin worker selection, WorkerAgent sandboxed execution with budget enforcement, VectorMemory search/remember operations with profile isolation, tool handler execution patterns (local + MCP), trace propagation across all layers, observability integration (OTEL/LangFuse/LangSmith), security boundaries (sandbox profiles, allowlists, budget ceilings), performance considerations (concurrency, memory management, observability overhead), debugging tips (trace correlation, memory inspection, routing verification), and testing guidance (unit + scenario tests). Includes complete flow diagram, security checklists, and links to 20+ related docs. See `docs/SYSTEM_EXECUTION_NARRATIVE.md`.
- **Clarified FastAPI's Architectural Role**: Created comprehensive documentation explicitly defining FastAPI as transport layer only (not orchestrator) to prevent mixing transport and orchestration concerns. Clarifies FastAPI's canonical responsibilities: HTTP/SSE transport (endpoints, streaming), authentication (X-Token validation), budget enforcement (AGENT_BUDGET_CEILING middleware), trace propagation (observability hooks), and request/response serialization. Documents what FastAPI must NOT do: planning logic (belongs in PlannerAgent), coordination decisions (belongs in CoordinatorAgent), tool execution (belongs in WorkerAgent), tool resolution (belongs in ToolRegistry), or memory operations (belongs in VectorMemory). Provides architectural layer diagram showing clear separation between transport (FastAPI) and orchestration (Planner/Coordinator/Workers), delegation patterns for synchronous planning/streaming execution/LangGraph integration, anti-patterns showing incorrect mixing of concerns, security boundary clarification (FastAPI enforces auth + budget, orchestration enforces profile isolation + tool allowlists), and testing implications (test transport and orchestration layers separately). Includes comparison table, code examples, and golden rule: "If it's not about HTTP transport, auth, or budget enforcement, it doesn't belong in FastAPI." See `docs/architecture/FASTAPI_ROLE.md`.
- **Added canonical RoutingAuthority**: Centralized routing decision authority eliminating distributed logic across coordinators, agents, and FastAPI endpoints. All routing decisions MUST go through `RoutingAuthority` with pluggable policies (round-robin, capability-based, load-balanced). Orchestrators delegate routing to `RoutingAuthority`, no routing bypass allowed. See `docs/orchestrator/ROUTING_AUTHORITY.md` and `src/cuga/orchestrator/routing.py`.
- **Added canonical Failure Modes and Retry Semantics**: Comprehensive failure taxonomy (`FailureMode`) categorizing agent/system/resource/policy/user errors with clear retryable/terminal/partial-success semantics. Introduced pluggable `RetryPolicy` (ExponentialBackoff/Linear/NoRetry) with auto-detection, jitter, circuit breaker integration. `PartialResult` preserves partial execution for recovery. See `docs/orchestrator/FAILURE_MODES.md` and `src/cuga/orchestrator/failures.py`.
- **Added canonical AgentLifecycleProtocol**: Clarified agent startup/shutdown expectations with idempotent, timeout-bounded, error-safe contracts. Defined state ownership boundaries (AGENT/MEMORY/ORCHESTRATOR) resolving ambiguity between ephemeral, persistent, and coordination state. See `docs/agents/AGENT_LIFECYCLE.md`, `docs/agents/STATE_OWNERSHIP.md`, and `src/cuga/agents/lifecycle.py`.
- **Added canonical AgentProtocol (I/O Contract)**: Standardized agent inputs (AgentRequest with goal/task/metadata/inputs/context/constraints) and outputs (AgentResponse with status/result/error/trace/metadata) eliminating special-casing in routing/orchestration. See `docs/agents/AGENT_IO_CONTRACT.md` and `src/cuga/agents/contracts.py`.
- Added guardrail enforcement utilities, sandbox allowlist, and coverage gating to 80%.
- Added CI enforcement so guardrail and registry diffs fail when documentation or changelog updates are missing.
- Introduced LangGraph-style planner/coordinator stack with trace propagation, vector memory retention, and FastAPI deployment surface.
- Registry defaults now wire budget/observability env keys with validated sandbox profiles, `/workdir` pinning for exec scopes, deterministic hot-reload ordering, and refreshed guardrail documentation/developer checklist.

### Added
- ➕ Added: Explicit `ExecutionContext` with 12 fields (trace_id, request_id, user_intent, user_id, memory_scope, conversation_id, session_id, profile, metadata, parent_context, created_at) replacing scattered implicit context. Immutable frozen dataclass with `with_*` update methods (with_user_intent/with_request_id/with_profile/with_metadata), validation (trace_id required, memory_scope requires user_id, conversation_id requires session_id), and serialization (to_dict/from_dict). Eliminates duplicate ExecutionContext in `src/cuga/agents/executor.py` — all code MUST import from `cuga.orchestrator.protocol`. Documented in `docs/orchestrator/EXECUTION_CONTEXT.md`.
- ➕ Added: Deterministic hashing embedder and pluggable vector backends with local search fallback.
- ➕ Added: Secure modular CLI for ingest/query/plan with trace propagation and JSON logs.
- ➕ Added: Guardrail checker and AGENTS.md SSOT for modular stack.
- ➕ Added: Modular `cuga.modular` package with planner/worker/tool/memory/observability scaffolding ready for LangGraph/LangChain
- ➕ Added: Vector memory abstraction with in-memory fallback and optional Chroma/Qdrant/Weaviate/Milvus connectors
- ➕ Added: LlamaIndex RAG loader/retriever utilities and Langfuse/OpenInference observability hooks
- ➕ Added: Developer tooling (.editorconfig, .gitattributes, pre-commit config, expanded Makefile) and CI workflow `ci.yml`
- ➕ Added: Watsonx Granite provider scaffold, Langflow component stubs, registry validation starter, and sandbox profile JSON.
- ➕ Added: Templates and documentation for `.env`, roadmap, and multi-agent examples under `agents/`, `tools/`, `memory/`, and `rag/`
- In development: GitHub Actions CI, coverage reports, Langflow project inspector
- ➕ Added: `scrape_tweets` MCP tool using `snscrape` for Twitter/X scraping
- ➕ Added: `extract_article` MCP tool powered by `newspaper4k` style extraction
- ➕ Added: `crypto_wallet` MCP tool wrapper for mnemonic, derivation, and signing flows
- ➕ Added: `moon_agents` MCP tool exposing agent templates and plan scaffolds
- ➕ Added: `vault_tools` MCP tool bundle for JSON queries, KV storage, and timestamps
- ➕ Added: CLI for listing agents, running goals, and exporting structured results
- ➕ Added: External tool plugin system with discovery helpers and a template plugin example
- ➕ Added: Env-gated MCP registry loader/runner wiring with sample `registry.yaml` and planner/executor integration
- ➕ Added: Watsonx model settings template with deterministic default parameters for Granite.
- ➕ Added: Agent UI intent preview, invocation timeline, and state badge for clearer tool legibility
- ➕ Added: Expanded guardrail verification script (`scripts/verify_guardrails.py`), inheritance markers, and CI enforcement
- ➕ Added: Guardrail verifier coverage for allowlist/denylist, budget, escalation, and redaction keywords plus planner/worker/coordinator contracts
- ➕ Added: Dual-mode LLM adapter layer with hybrid routing, budget guardrails, and config/env precedence
- ➕ Added: Architecture/registry observability documentation set (overview, registry, tiers, sandboxes, compose, ADR, glossary)
- ➕ Added: MCP v2 registry slice with immutable snapshot models, YAML loader, and offline contract tests

### Changed
- 🔁 Changed: Planner, coordinator, worker, and RAG pipelines to enforce profile/trace propagation and round-robin fairness.
- 🔁 Changed: Dynamic tool imports hardened to `cuga.modular.tools.*` namespace with explicit errors.
- 🔁 Changed: Centralized MCP server utilities for payload handling and sandbox lookup
- 🔁 Changed: Planner now builds multi-step plans with cost/latency optimization, logging, and trace outputs
- 🔁 Changed: Controller and executor now emit structured audit traces and sanitize handler failures
- 🔁 Changed: Tool registry now deep-copies resolved entries and profile snapshots to prevent caller mutations from leaking between tools
- 🔁 Changed: Reconciled agent lifecycle, tooling, and security documentation with current code enforcement boundaries
- 🔁 Changed: Guardrail hierarchy documented explicitly in root/docs `AGENTS.md` with inheritance reminders.
- 🔁 Changed: Guardrail routing updated so root `AGENTS.md` remains canonical with per-directory inherit markers
- 🔁 Changed: Guardrail verification now centralizes allowlists/keywords and supports env overrides to reduce drift
- 🔁 Changed: Guardrail verification now tracks `config/` with inheritance markers to cover Hydra registry defaults
- 🔁 Changed: Root `AGENTS.md` reorganized to align Tier 1 defaults with registry tool swaps, sandbox pinning, and budget/redaction guardrails
- 🔁 Changed: Pytest default discovery now targets `tests/`, with docs/examples suites run through dedicated scripts and build artifacts ignored by default
- 🔁 Changed: Pytest `norecursedirs` now retains default exclusions (e.g., `.*`, `venv`, `dist`, `*.egg`) to avoid unintended test discovery
- 🔁 Changed: LLM adapter can run atop LiteLLM by default with hardened retries, fallback error handling, and thread-safe budget warnings
- 🔁 Changed: MCP registry loader now uses Hydra's `compose` API for Hydra/OmegaConf configuration composition with shared config defaults and fragment support
- 🔁 Changed: Watsonx Granite provider now validates credentials up front, enforces deterministic defaults, and writes structured audit metadata (timestamp, actor, parameters, outcome).
- 🔁 Changed: Tool registry loader parses files by extension (YAML/JSON) with optional schema validation guarded by dependency detection.
- 🔁 Changed: JSON Schema validation now guards registry parsing with structured logging and skips malformed entries instead of failing globally.
- 🔁 Changed: Watsonx function-call validation now fails fast by default with optional legacy graceful mode.

### Fixed
- 🐞 Fixed: Hardened `crypto_wallet` parameter parsing and clarified non-production security posture
- 🐞 Fixed: `extract_article` dependency fallback now respects missing `html` inputs
- 🐞 Fixed: `moon_agents` no longer returns sandbox filesystem paths
- 🐞 Fixed: `vault_tools` KV store now uses locked, atomic writes to avoid race conditions
- 🐞 Fixed: `vault_tools` detects corrupt stores, enforces locking support, and writes under held locks
- 🐞 Fixed: `vault_tools` KV store writes use fsynced temp files to preserve atomic persistence safety
- 🐞 Fixed: `_shared` CLI argument parsing now errors when `--json` is missing a value
- 🐞 Fixed: `crypto_wallet` narrows `word_count` parsing errors to expected types
- 🐞 Fixed: `_shared.load_payload` narrows JSON parsing exceptions for clearer diagnostics
- 🐞 Fixed: `extract_article` fallback parsing now only triggers for expected extraction or network failures
- 🐞 Fixed: Guardrail checker git diff detection now validates git refs and uses fixed git diff argv to avoid unchecked subprocess input
- 🐞 Fixed: Tier table generation now falls back to env keys for non-placeholder values to avoid leaking secrets in docs
- 🐞 Fixed: MCP registry loader enforces enabled-aware duplicate detection, method/path type validation (including `operation_id`), and environment variables that override disabled entries when set
- 🐞 Fixed: Guard modules deduplicated under a shared orchestrator to keep routing logic consistent across inputs, tools, and outputs.

### Documentation
- 📚 Rewrote README/USAGE/AGENTS/CONTRIBUTING/SECURITY with 2025 agent-stack guidance and integration steps
- 📚 Documented: Branch cleanup workflow and issue stubs for consolidating Codex branches
- 📚 Documented: Root guardrails, audit expectations, and routing table for guardrail updates
- 📚 Documented: Guardrail verification and change-management checklist in AGENTS/README plus alignment reminder in `todo1.md`
- 📚 Documented: Hydra-based registry composition (env overrides, enabled-only duplicate detection) and linked MCP integration guidance
- 📚 Documented: Refined canonical `AGENTS.md` with quick checklist, local template, and cross-links to policy docs
- 📚 Documented: Architecture topology (controller/planner/tool bus), orchestration modes, and observability enhancements
- 📚 Documented: STRIDE-lite threat model and red-team checklist covering sandbox escape, prompt injection, and leakage tests
- 📚 Documented: Usage and testing quick-start guides plus repository Code of Conduct and security policy
- 📚 Documented: Langflow guard components now use `lfx.*` imports with unique identifiers; registry and watsonx docs refreshed for extension-aware parsing and audit trails.

### Testing
- 🧪 Added: Unit tests for vector search scoring, planning relevance, round-robin dispatch, env parsing, and CLI flow.
- 🧪 Added: Expanded `scrape_tweets` test coverage for limits, dependencies, and health checks
- 🧪 Added: Offline MCP registry, runner, and planner/executor tests backed by FastAPI mock servers
- 🧪 Added: Dedicated lint workflow running Ruff and guardrail verification on pushes and pull requests

---

## [v1.0.0] - Initial Production Release

🎉 This is the first production-ready milestone for the `cugar-agent` framework.

### ✨ Added
- Modular agent pipeline:
  - `controller.py` – agent orchestration
  - `planner.py` – plan step generator
  - `executor.py` – tool execution
  - `registry.py` – tool registry and sandboxing
- Profile-based sandboxing with scoped tool isolation
- MCP-ready integrations and registry templating
- Profile fragment resolution logic (relative to profile path)
- PlantUML message flow for documentation
- Developer-friendly `Makefile` for env, profile, and registry tasks
- Initial tests in `tests/` for agent flow verification
- ➕ Added: Profile policy enforcer with schema validation and per-profile templates under `configurations/policies`

### 🛠️ Changed
- Standardized folder structure under `src/cuga/`
- Updated `.env.example` for MCP setup

### 📚 Documentation
- Rewritten `AGENTS.md` as central contributor guide
- Added structure for:
  - `agent-core.md`
  - `agent-config.md`
  - `tools.md`
- Registry merge guide in `docs/registry_merge.md`
- Security policy in `docs/Security.md`
- ➕ Added: `docs/policies.md` describing policy authoring and enforcement flow

### ⚠️ Known Gaps
- CLI runner may need test scaffolding
- Tool schema validation needs stronger contract enforcement
- Logging verbosity defaults may need hardening

---

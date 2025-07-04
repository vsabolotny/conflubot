# CLEAN CODE GUIDELINES (Python Backend + API + LLM)

## Project Structure
```
project/
├── app/
│   ├── api/                 # Route definitions and request/response schemas
│   ├── services/            # Business logic
│   ├── llm/                 # LLM integrations
│   ├── models/              # Pydantic or ORM models
│   ├── database/            # Database models and migrations
│   ├── repositories/        # Data access layer
│   ├── middleware/          # Authentication, rate limiting, CORS
│   ├── utils/               # Shared utilities and helpers
│   ├── config.py            # Configuration loader
│   ├── main.py              # Entry point
├── tests/                   # Unit and integration tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/              # Database schema migrations
├── requirements.txt         # Dependencies
├── requirements-dev.txt     # Development dependencies
├── .env                     # Secrets and environment vars
├── .pre-commit-config.yaml  # Pre-commit configuration
└── CLEAN_CODE.md            # This file
```

## General Principles

- Write readable, predictable, and testable code.
- Prefer explicitness over cleverness.
- Separate I/O from business logic.
- Use type hints everywhere.
- Keep functions pure and short (≤ 20 lines for pure functions, ≤ 50 for complex business logic).
- Follow 12-Factor App principles.
- Implement security-first design patterns.

## Modules & Organization

- One responsibility per module (api, services, llm, etc.)
- Avoid circular imports: keep dependencies flowing one way.
- Expose only what is needed with __all__ or public interfaces.
- Use repository pattern to abstract database operations.
- Keep ORM models separate from Pydantic models.

## API Layer

- Use Pydantic models for request/response validation.
- Apply dependency injection for services and settings.
- Validate data early — reject bad inputs at the boundary.
- Return structured, predictable errors (e.g., JSON with error codes).
- Implement rate limiting for all endpoints.
- Add input size limits to prevent DoS attacks.
- Include health check endpoints for monitoring.

Example:
```python
@router.post("/ask")
async def ask_question(
    request: AskRequest, 
    service: AskService = Depends(),
    current_user: User = Depends(get_current_user)
):
    return await service.ask(request.question, user_id=current_user.id)
```

## Business Logic Layer

- Keep logic in services/, not in routes.
- Use plain Python (no unnecessary framework dependencies).
- Make services stateless or inject state (e.g., database, cache).
- Split large service functions into helper classes or commands.
- Use async/await consistently throughout the stack.
- Handle database transactions for multi-step operations.

## Database & Repository Layer

- Use repository pattern for data access:
```python
class UserRepository:
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    async def create(self, user_data: UserCreate) -> User:
        pass
```
- Keep database models separate from API models.
- Use database connection pooling.
- Implement proper transaction management.

## LLM Integration Layer

- Use a clear interface for any LLM:
```python
class LLMClient:
    async def complete(self, prompt: str) -> LLMResponse:
        pass
```
- Support mocking for unit tests (use FakeLLMClient).
- Log all LLM interactions for debugging and auditing.
- Handle retries, timeouts, rate-limiting gracefully.
- Implement token counting and cost tracking:
```python
class LLMUsageTracker:
    def track_usage(self, prompt_tokens: int, completion_tokens: int, model: str):
        pass
```
- Validate LLM responses for harmful content and formatting.
- Use semaphores to control concurrent LLM requests.

## Security & Validation

- Implement authentication/authorization middleware.
- Sanitize all inputs to prevent SQL injection and XSS.
- Use parameterized queries for database operations.
- Validate file uploads and limit file sizes.
- Implement CORS policies appropriately.
- Use HTTPS in production.
- Store secrets securely (never in code).

## Testing

- Use pytest and pytest-asyncio for async code.
- Follow Arrange–Act–Assert pattern.
- Mock external services (LLMs, DBs, APIs).
- Use factories or fixtures to generate test data.
- Implement integration tests for critical paths.
- Test error scenarios and edge cases.
- Maintain test coverage above 80%.

## Error Handling

- Catch only specific exceptions.
- Add context to errors before re-raising.
- Avoid except: pass unless explicitly documented.
- Convert system errors into meaningful API errors.
- Implement global exception handlers.
- Log errors with sufficient context for debugging.

## Configuration & Environment

- Load config from .env or environment variables only.
- Centralize all config access in config.py.
- Avoid hardcoding secrets or keys in code.
- Use different configurations for dev/staging/prod.
- Validate configuration on startup.

## Logging & Monitoring

- Use logging module, not print().
- Implement structured JSON logging for production.
- Add correlation IDs to trace requests across services.
- Log LLM usage, costs, and performance metrics.
- Include request/response times in logs.
- Set up proper log levels (DEBUG, INFO, WARNING, ERROR).

## Observability

- Implement health check endpoints.
- Use OpenTelemetry for distributed tracing.
- Add metrics for:
  - API response times
  - LLM request latency
  - Error rates
  - Database query performance
  - Token usage and costs

## Async/Concurrency

- Use async/await consistently throughout the stack.
- Handle concurrent LLM requests with proper semaphores.
- Use connection pooling for databases and external APIs.
- Implement timeout handling for all external calls.
- Use asyncio.gather() for parallel operations where appropriate.

## Linting, Formatting, Tools

- Use black for formatting.
- Use ruff or flake8 for linting.
- Use mypy for static typing checks.
- Use bandit for security scanning.
- Use safety for dependency vulnerability scanning.
- Use pre-commit to enforce all checks before every commit:
  - Run tests
  - Security scans
  - Dependency checks
  - Code formatting
  - Type checking

## Examples of Clean Code Patterns

**Clear naming:**
```python
async def generate_summary_from_documents(
    documents: List[Document], 
    max_tokens: int = 1000
) -> Summary:
    pass
```

**Avoid magic values:**
```python
# Bad
timeout = 30

# Good
DEFAULT_LLM_TIMEOUT_SECONDS = 30
MAX_PROMPT_LENGTH = 4000
```

**Dependency injection:**
```python
class DocumentService:
    def __init__(
        self, 
        llm_client: LLMClient,
        document_repo: DocumentRepository,
        usage_tracker: LLMUsageTracker
    ):
        self.llm_client = llm_client
        self.document_repo = document_repo
        self.usage_tracker = usage_tracker
```

**Keep controllers thin:**
```python
@router.post("/summarize")
async def summarize_document(
    request: SummarizeRequest,
    service: DocumentService = Depends()
):
    return await service.summarize(request.document_id)
```

**Error handling with context:**
```python
try:
    response = await self.llm_client.complete(prompt)
except LLMTimeoutError as e:
    logger.error(f"LLM timeout for user {user_id}: {e}")
    raise ServiceUnavailableError("AI service temporarily unavailable")
```

**Repository pattern:**
```python
class PostgreSQLUserRepository(UserRepository):
    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            return User(**row) if row else None
```

## Production Deployment

- Use environment-specific configuration files.
- Implement graceful shutdown handling.
- Use container orchestration (Docker + Kubernetes).
- Set up monitoring and alerting.
- Implement circuit breakers for external services.
- Use CDN for static assets.
- Implement database migrations strategy.
- Set up automated backups.

## Performance Optimization

- Use database indexing appropriately.
- Implement caching for frequently accessed data.
- Use connection pooling for all external services.
- Optimize LLM prompts for cost and performance.
- Implement pagination for large datasets.
- Use async processing for heavy operations.
- Monitor and optimize database queries.
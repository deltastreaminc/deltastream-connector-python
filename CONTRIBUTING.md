### Contributing

Thank you for contributing to the DeltaStream Python client.

#### Prerequisites

- Python 3.11+
- `uv` for dependency management
- OpenAPI Generator CLI available via one of:
  - Homebrew: `brew install openapi-generator`
  - NPM: `npx @openapitools/openapi-generator-cli`
  - Docker image: `openapitools/openapi-generator-cli`

Install dependencies:

```bash
make install
```

#### Regenerating the controlplane OpenAPI client (apiv2)

The OpenAPI spec lives at `src/deltastream/api/controlplane/api-server-v2.yaml`.
The generator script is at `scripts/generate_apiv2.py`.

Run the generator:

```bash
uv run python scripts/generate_apiv2.py
```

Notes:
- Output is generated into `src/deltastream/api/controlplane/openapi_client` (in-place).
- The command supports Homebrew/NPM/Docker CLI variants automatically.
- The script is excluded from the built package distribution.

#### Tests / Lint / Types

```bash
make test           # Run all tests
make lint           # Run linting checks
make format         # Format code
make mypy           # Run type checking
make ci             # Run all CI checks (lint, format, mypy, unit-tests, build)
```

For additional options:
```bash
make unit-tests     # Run unit tests only (exclude integration tests)
make check-format   # Check if code formatting is correct
make build          # Build the package
make clean          # Clean build artifacts
make help           # Show all available targets
```

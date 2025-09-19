### Contributing

Thank you for contributing to the DeltaStream Python client.

#### Prerequisites

- Python 3.11+
- `uv` for dependency management
- OpenAPI Generator CLI available via one of:
  - Homebrew: `brew install openapi-generator`
  - NPM: `npx @openapitools/openapi-generator-cli`
  - Docker image: `openapitools/openapi-generator-cli`

Sync dependencies:

```bash
uv sync
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
uv run pytest
uv run ruff check --fix
uv run ruff format
uv run mypy
```



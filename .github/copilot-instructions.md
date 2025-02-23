# deltastream driver
# Project Context
A Python client library for [DeltaStream](https://deltastream.io) - a SQL streaming processing engine based on Apache Flink.
# Code Style and Structure
- Write concise, technical Python, SQL or Jinja code with accurate examples
- Use functional and declarative programming patterns; avoid classes
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., isLoading, hasError)
- Structure repository files as follows:
.
├── src/                          # Source code root directory
│   └── deltastream/              # Main package namespace
│       └── api/                  # API client implementation
│           
└── tests/                        # Test suite root directory
    └── api/                      # API tests
        ├── controlplane/         # Tests for control plane operations
        └── dataplane/           # Tests for data plane operations

# Build and project setup
The project is using `uv` for dependency management. You can find the lockfile in `uv.lock`.
To run tests, use `uv run pytest <path_to_test>`.
To add dependencies use `uv add <package>`.
Dependency resolution is done using `uv sync`.
Dependencies are specified in `pyproject.toml`.
Dependencies are installed in `./.venv`.
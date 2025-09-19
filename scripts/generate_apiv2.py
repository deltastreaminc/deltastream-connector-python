from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


def _find_openapi_generator() -> List[str]:
    """Return the base command to run OpenAPI Generator.

    Prefers the `openapi-generator` binary (Homebrew install),
    falls back to `openapi-generator-cli` if available.
    """
    candidates = ["openapi-generator", "openapi-generator-cli"]
    for candidate in candidates:
        if shutil.which(candidate):
            return [candidate]

    # Optional: support docker if available and the image exists locally
    if shutil.which("docker"):
        return [
            "docker",
            "run",
            "--rm",
            "-u",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{Path.cwd()}:{Path.cwd()}",
            "-w",
            f"{Path.cwd()}",
            "openapitools/openapi-generator-cli",
        ]

    raise FileNotFoundError(
        "OpenAPI Generator CLI not found. Install with `brew install openapi-generator` "
        "or use `npx @openapitools/openapi-generator-cli`, or ensure Docker image "
        "openapitools/openapi-generator-cli is available."
    )


def main() -> int:
    """Generate the controlplane OpenAPI Python client in-place.

    This regenerates `deltastream.api.controlplane.openapi_client` from
    `src/deltastream/api/controlplane/api-server-v2.yaml`.
    """
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "src"
    spec_path = src_dir / "deltastream/api/controlplane/api-server-v2.yaml"

    if not spec_path.exists():
        print(f"Spec file not found: {spec_path}", file=sys.stderr)
        return 1

    base_cmd = _find_openapi_generator()

    # Use python generator with pydantic v2 and lazy imports
    cmd = base_cmd + [
        "generate",
        "-i",
        str(spec_path),
        "-g",
        "python",
        "-o",
        str(src_dir),  # generate inside src so package path is respected
        "--skip-validate-spec",
        "--additional-properties",
        (
            "generateSourceCodeOnly=true,"
            "lazyImport=true,"
            "enumClassPrefix=true,"
            "modelPropertyNaming=original,"
            "packageName=deltastream.api.controlplane.openapi_client"
        ),
    ]

    # Ensure output dir exists
    (src_dir / "deltastream").mkdir(parents=True, exist_ok=True)

    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(
            f"OpenAPI Generator failed with exit code {exc.returncode}", file=sys.stderr
        )
        return exc.returncode

    print("OpenAPI client regenerated at: deltastream/api/controlplane/openapi_client")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

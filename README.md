# deltastream-connector

A Python client library for [DeltaStream](https://deltastream.io) - a SQL streaming processing engine based on Apache Flink.

## Features

- Asynchronous API client for DeltaStream
- Support for SQL statements execution
- Streaming result sets
- File attachments for SQL queries (e.g., JAR files for UDFs)
- API Token authentication
- Python 3.11+ support

## Installation

```bash
pip install deltastream-connector
```

## Quick Start

```python
import asyncio
from deltastream.api.conn import APIConnection

# Initialize connection with API token
auth_token = os.getenv("DELTASTREAM_AUTH_TOKEN")

if not auth_token:
    raise ValueError("Environment variable 'DELTASTREAM_AUTH_TOKEN' is not set")

# Use the token to construct the DSN and create the connection
dsn = f"https://:{auth_token}@api.deltastream.io/v2"
conn = APIConnection.from_dsn(dsn)

async def main():
    # Execute SQL queries
    rows = await conn.query("SELECT 1;")
    
    # Process results asynchronously
    async for row in rows:
        print(row)

if __name__ == '__main__':
    asyncio.run(main())
```

## File Attachments

The connector provides convenient helper functions to attach files (like JAR files for UDFs) to SQL queries without manually creating blob objects.

### Simple File Attachment

```python
import asyncio
from deltastream.api.conn import APIConnection

async def main():
    conn = APIConnection.from_dsn("https://:{token}@api.deltastream.io/v2")
    
    # Create a function source with a JAR file attachment
    await conn.exec_with_files(
        "CREATE FUNCTION_SOURCE \"my_udf\" WITH ('file' = 'my_function.jar', 'description' = 'My custom UDF');",
        ["/path/to/my_function.jar"]
    )
    
    # Query function sources and get results
    rows = await conn.query_with_files("SHOW FUNCTION_SOURCES;")
    async for row in rows:
        print(f"Function: {row[0]}, Status: {row[1]}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Advanced File Attachment Configuration

```python
# Custom file names and content types
await conn.exec_with_files(
    "CREATE FUNCTION_SOURCE \"advanced_udf\" WITH ('file' = 'custom_name.jar');",
    [{
        "path": "/path/to/actual_file.jar",
        "name": "custom_name.jar",
        "content_type": "application/java-archive"
    }]
)

# Multiple files
await conn.exec_with_files(
    "CREATE FUNCTION_SOURCE \"multi_file_udf\" WITH ('file' = 'main.jar', 'lib' = 'dependency.jar');",
    [
        "/path/to/main.jar",
        {"path": "/path/to/lib.jar", "name": "dependency.jar"}
    ]
)
```

## Authentication

The connector uses API token authentication. You can obtain an API token from the DeltaStream platform by running `CREATE API_TOKEN api_token_name;` using the console.

## Support

For support, please contact support@deltastream.com or open an issue on our [GitHub repository](https://github.com/deltastreaminc/deltastream-connector/issues).
# deltastream-connector

A Python client library for [DeltaStream](https://deltastream.io) - a SQL streaming processing engine based on Apache Flink.

## Features

- Asynchronous API client for DeltaStream
- Support for SQL statements execution
- Streaming result sets
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

## Authentication

The connector uses API token authentication. You can obtain an API token from the DeltaStream platform by running `CREATE API_TOKEN api_token_name;` using the console.

## Support

For support, please contact support@deltastream.com or open an issue on our [GitHub repository](https://github.com/deltastreaminc/deltastream-connector/issues).
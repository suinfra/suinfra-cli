import json

import httpx

from suinfra_cli import DATA_DIR
from suinfra_cli.models import RpcEndpoint


def load_rpc_urls() -> dict[str, str]:
    with open(DATA_DIR / "rpc_urls.json", "r") as f:
        return json.loads(f.read())


async def fetch_rpc_endpoints(
    url: str,
) -> list[RpcEndpoint]:
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
    return [RpcEndpoint(**rpc) for rpc in r.json()]


def calculate_percentile(
    data: list[int],
    percentile: int,
):
    if not data:
        return None

    data.sort()
    k = (len(data) - 1) * (percentile / 100)
    f = int(k)
    c = k - f

    if f + 1 < len(data):
        return data[f] + (c * (data[f + 1] - data[f]))
    else:
        return data[f]

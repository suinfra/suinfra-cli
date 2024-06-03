import json
import random
import statistics
import time
import uuid
from collections import defaultdict
from math import ceil

import httpx
import trio
import typer
from bunnet import init_bunnet
from pymongo import MongoClient
from rich import print

from suinfra_cli import DB_URL, DEFAULT_RPCS_JSON_FILE_URL, REGION
from suinfra_cli.models import (
    Db_RpcPingResult,
    Db_RpcPingTest,
    RpcEndpoint,
    RpcPingResult,
)
from suinfra_cli.utils import calculate_percentile, fetch_rpc_endpoints

app = typer.Typer()


async def make_rpc_request(
    http_client: httpx.AsyncClient,
    rpc_endpoint: RpcEndpoint,
    nonce: int,
) -> httpx.Response:
    """
    Make an RPC request to the given endpoint.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "suinfra",
    }

    if rpc_endpoint.auth_header:
        headers[rpc_endpoint.auth_header.key] = rpc_endpoint.auth_header.value

    r = await http_client.post(
        rpc_endpoint.rpc_url,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": nonce,
            "method": "suix_getReferenceGasPrice",
            "params": [],
        },
    )

    if r.status_code != 200:
        print(r.status_code, r.json())

    return r


@app.command()
def fetch(
    url: str = typer.Argument(
        DEFAULT_RPCS_JSON_FILE_URL,
        help="URL pointing to an rpcs.json file.",
    ),
):
    """
    Fetch the list of current RPC endpoints.
    """
    rpc_endpoints = trio.run(fetch_rpc_endpoints, url)
    print(
        json.dumps(
            [rpc.model_dump() for rpc in rpc_endpoints],
            indent=4,
        )
    )
    return


@app.command()
def cleanup():
    """
    Clean up test instances with no associated test results.
    """
    client = MongoClient(DB_URL)
    init_bunnet(
        database=client["suinfra-production"],
        document_models=[
            Db_RpcPingResult,
            Db_RpcPingTest,
        ],
    )

    tests = Db_RpcPingTest.find_all().to_list()

    for test in tests:
        result_count = Db_RpcPingResult.find(
            Db_RpcPingResult.test_id == test.id
        ).count()
        if result_count == 0:
            print(f"Deleting test {test.id}")
            test.delete()

    return


@app.command()
def ping(
    iterations: int = typer.Option(
        10,
        help="Number of times to ping each RPC URL.",
    ),
    sleep: int = typer.Option(
        1000,
        help="Time to sleep in ms between pings.",
    ),
    timeout: int = typer.Option(
        120,
        help="Timeout for the ping test.",
    ),
    test_id: str = typer.Option(
        None,
        help="Test ID for the ping test.",
    ),
    write_to_db: bool = typer.Option(
        False,
        help="Write results to the database.",
    ),
    rpcs_json_url: str = typer.Option(
        DEFAULT_RPCS_JSON_FILE_URL,
        help="URL pointing to an RPCs JSON file.",
    ),
):
    """
    Ping all RPC nodes asynchronously.
    """

    async def _ping_rpc_node(
        rpc_endpoint: RpcEndpoint,
        iterations: int = 10,
        sleep_time: int = 1,
        results: list[RpcPingResult] = [],
    ):
        print(f"Starting ping test for {rpc_endpoint.name}...")

        http_client = httpx.AsyncClient(timeout=10)

        ping_latencies = []

        async def ping_once():
            try:
                start_time = trio.current_time()
                random.seed(start_time)
                nonce = random.getrandbits(8)
                r = await make_rpc_request(http_client, rpc_endpoint, nonce)
                if r.status_code == 200:
                    end_time = trio.current_time()
                    latency = end_time - start_time
                    ping_latencies.append(latency)
                else:
                    print(f"Failed to ping {rpc_endpoint.name}: {r.status_code}")
            except Exception as e:
                print(e)

            return

        # Prime connection by pinging once.
        await ping_once()

        async with trio.open_nursery() as nursery:
            for _ in range(iterations):
                nursery.start_soon(ping_once)
                await trio.sleep(sleep_time / 1000)

        if len(ping_latencies) > 0:
            ping_result = RpcPingResult(
                rpc_name=rpc_endpoint.name,
                rpc_url=rpc_endpoint.rpc_url,
                avg_latency=ceil(statistics.mean(ping_latencies) * 1000),
                p10_latency=ceil(calculate_percentile(ping_latencies, 10) * 1000),
                p50_latency=ceil(calculate_percentile(ping_latencies, 50) * 1000),
                p90_latency=ceil(calculate_percentile(ping_latencies, 90) * 1000),
                st_dev=ceil(statistics.stdev(ping_latencies) * 1000),
                from_region=REGION,
            )
            results.append(ping_result)

        return

    if iterations < 2:
        raise typer.Exit("Iterations must be greater than or equal to 2.")

    if write_to_db and not DB_URL:
        raise typer.Exit("DB_URL env var was not found.")

    rpc_endpoints = trio.run(fetch_rpc_endpoints, rpcs_json_url)
    timestamp = int(time.time())

    print(f"Pinging {len(rpc_endpoints)} RPC endpoints from region {REGION}!")
    print(f"Iterations: {iterations}")
    print(f"Sleep Time: {sleep}ms\n")

    results: list[RpcPingResult] = []

    async def parent():
        with trio.move_on_after(timeout):  # Timeout after 120 seconds.
            try:
                async with trio.open_nursery() as nursery:
                    for rpc_endpoint in rpc_endpoints:
                        nursery.start_soon(
                            _ping_rpc_node,
                            rpc_endpoint,
                            iterations,
                            sleep,
                            results,
                        )
            except* KeyError as excgroup:
                for exc in excgroup.exceptions:
                    print(exc)

    trio.run(parent)

    print(results)

    if len(results) == 0:
        return

    results.sort(key=lambda x: x.avg_latency)

    if write_to_db:
        print("Writing results to the database...")

        client = MongoClient(DB_URL)
        init_bunnet(
            database=client["suinfra-production"],
            document_models=[
                Db_RpcPingResult,
                Db_RpcPingTest,
            ],
        )

        if test_id:
            print(f"Test ID: {test_id}")
            rpc_ping_test = Db_RpcPingTest.get(uuid.UUID(test_id))
            if not rpc_ping_test:
                raise typer.Exit("Test ID not found.")
        else:
            rpc_ping_test = Db_RpcPingTest(
                id=uuid.uuid4(),
                timestamp=timestamp,
            )
            rpc_ping_test.save()

        ping_results = [
            Db_RpcPingResult(
                id=f"{result.rpc_name}::{result.from_region}::{timestamp}",
                rpc_name=result.rpc_name,
                rpc_url=result.rpc_url,
                avg_latency=result.avg_latency,
                p10_latency=result.p10_latency,
                p50_latency=result.p50_latency,
                p90_latency=result.p90_latency,
                st_dev=result.st_dev,
                from_region=result.from_region,
                test_id=uuid.UUID(test_id),
            )
            for result in results
        ]
        Db_RpcPingResult.insert_many(ping_results)

    return


@app.command()
def tests():
    client = MongoClient(DB_URL)
    init_bunnet(
        database=client["suinfra-production"],
        document_models=[
            Db_RpcPingResult,
            Db_RpcPingTest,
        ],
    )

    rpc_ping_test = Db_RpcPingTest.find().first_or_none()
    rpc_ping_results = Db_RpcPingResult.find(Db_RpcPingResult.test_id == rpc_ping_test.id).to_list()  # fmt: skip

    result_dict = defaultdict(list[Db_RpcPingResult])

    for result in rpc_ping_results:
        result_dict[result.from_region].append(result)

    for key in result_dict:
        result_dict[key] = sorted(result_dict[key], key=lambda x: x.avg_latency)

    for region, results in result_dict.items():
        print(f"Region: {region}")
        for result in results:
            print(f"{result.rpc_name} - {result.avg_latency}ms")
        print("")

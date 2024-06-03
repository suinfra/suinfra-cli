import time
import uuid

import httpx
import trio
import typer
from bunnet import init_bunnet
from pymongo import MongoClient

from suinfra_cli import DB_NAME, DB_URL, FLY_AUTH_TOKEN, FLY_IMAGE_ID
from suinfra_cli.models import Db_RpcPingResult, Db_RpcPingTest

FLY_REGIONS = [
    "ams",
    "arn",
    "atl",
    "bog",
    "bom",
    "bos",
    "cdg",
    "den",
    "dfw",
    "eze",
    "ewr",
    "fra",
    "gdl",
    "gig",
    "gru",
    "hkg",
    "iad",
    "jnb",
    "lax",
    "lhr",
    "mad",
    "mia",
    "nrt",
    "ord",
    "otp",
    "phx",
    "qro",
    "scl",
    "sea",
    "sin",
    "sjc",
    "syd",
    "waw",
    "yul",
    "yyz",
]


app = typer.Typer()


async def start_machine(
    client: httpx.AsyncClient,
    iterations: int,
    region: str,
    test_id: str,
    vm_cpus: int,
    vm_kind: str,
    vm_memory: int,
):
    print(f"Starting worker in {region}...")

    url = "https://api.machines.dev/v1/apps/suinfra-cli/machines"
    payload = {
        "config": {
            "auto_destroy": True,
            "guest": {
                "cpu_kind": vm_kind,
                "cpus": vm_cpus,
                "memory_mb": vm_memory,
            },
            "image": FLY_IMAGE_ID,
            "init": {
                "cmd": [
                    "run",
                    "suinfra",
                    "rpc",
                    "ping",
                    "--iterations",
                    f"{iterations}",
                    "--test-id",
                    f"{test_id}",
                    "--write-to-db",
                ],
            },
            "restart": {
                "policy": "no",
            },
        },
        "region": region,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FLY_AUTH_TOKEN}",
    }

    response = await client.post(url, json=payload, headers=headers)
    print(response.json())


@app.command()
def rpc(
    image_id: str = typer.Argument(FLY_IMAGE_ID, help="Fly image ID."),
    iterations: int = typer.Option(30, help="Number of iterations."),
    vm_cpus: int = typer.Option(2, help="Number of CPUs."),
    vm_kind: str = typer.Option("shared", help="CPU kind (shared or performance)."),
    vm_memory: int = typer.Option(1024, help="Number of CPUs."),
):
    """
    Run a suinfra-cli command in multiple regions on Fly.
    """

    # rpc_endpoints = trio.run(fetch_rpc_endpoints, rpc_list)
    # rpc_endpoints_json = json.dumps([rpc.model_dump() for rpc in rpc_endpoints])
    # rpc_endpoints_b64_str = base64.b64encode(rpc_endpoints_json.encode()).decode()

    if not image_id:
        raise typer.Exit("Image ID is required.")

    client = MongoClient(DB_URL)
    init_bunnet(
        database=client[DB_NAME],
        document_models=[
            Db_RpcPingResult,
            Db_RpcPingTest,
        ],
    )

    # Initialize the ping test.
    rpc_ping_test = Db_RpcPingTest(
        id=uuid.uuid4(),
        timestamp=int(time.time()),
    )
    rpc_ping_test.save()

    typer.confirm(f"Test ID: {rpc_ping_test.id}. Start the test?", abort=True)

    async def parent():
        client = httpx.AsyncClient(timeout=60)
        async with trio.open_nursery() as nursery:
            for region in FLY_REGIONS:
                nursery.start_soon(
                    start_machine,
                    client,
                    iterations,
                    region,
                    str(rpc_ping_test.id),
                    vm_cpus,
                    vm_kind,
                    vm_memory,
                )

    trio.run(parent)

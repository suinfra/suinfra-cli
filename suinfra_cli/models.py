from uuid import UUID

from bunnet import Document
from pydantic import BaseModel


class RpcEndpoingAuthHeader(BaseModel):
    key: str
    value: str


class RpcEndpoint(BaseModel):
    name: str
    provider_url: str | None = None
    rpc_url: str
    auth_header: RpcEndpoingAuthHeader | None = None


class TxResult(BaseModel):
    digest: str
    avg_latency: int
    p10_latency: int
    p50_latency: int
    p90_latency: int
    st_dev: int
    from_region: str


class RpcPingResult(BaseModel):
    rpc_name: str
    rpc_url: str
    avg_latency: int
    p10_latency: int
    p50_latency: int
    p90_latency: int
    st_dev: int
    from_region: str


class Db_RpcPingTest(Document):
    id: UUID
    timestamp: int

    class Settings:
        name = "rpc_ping_tests"


class Db_RpcPingResult(Document):
    id: str
    rpc_name: str
    rpc_url: str
    avg_latency: int
    p10_latency: int
    p50_latency: int
    p90_latency: int
    st_dev: int
    from_region: str
    test_id: UUID

    class Settings:
        name = "rpc_ping_results"

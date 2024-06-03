import typer

from suinfra_cli.commands import benchmark, rpc

app = typer.Typer()

app.add_typer(benchmark.app, name="benchmark")
app.add_typer(rpc.app, name="rpc")

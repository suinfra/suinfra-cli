# Suinfra CLI

The Suinfra CLI provides a command-line interface to trigger global Sui RPC benchmark tests in 35 regions around the world. Currently, the Suinfra CLI is capable of conducting RPC latency benchmark testing, and we are working on adding support for E2E transaction latency testing as well. The Suinfra benchmarking solution is economical, fast, and globally distributed. Our tool provisions servers on demand (with a cold start of less than 1 second), and finishes within 1 minute in 35 regions.

# How it Works

The Suinfra CLI is structured as a command-line tool that can be built into a Docker image via the provided Dockerfile, and subsequently deployed to [Fly.io](https://fly.io). The logic for pinging RPC nodes can be found in the `ping()` function in [this file](https://github.com/suinfra/suinfra-cli/blob/main/suinfra_cli/commands/rpc.py). The logic for launching servers in 35 regions around the world can be found in [this file](https://github.com/suinfra/suinfra-cli/blob/main/suinfra_cli/commands/benchmark.py).

# What's Next?

Right now, the benchmarking logic is tightly coupled with the CLI logic. Over the next few weeks, we'll be working on separating the benchmarking logic into a separate `suinfra-sdk`. At that point, this CLI will be refactored to use `suinfra-sdk` as a core dependency.
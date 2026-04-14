# Architecture

Qorme uses a domain-driven approach.

Each `Domain` is responsible of some functionality.

`Domain`s are configurable via the `Config` class, initialized from project settings.

A singleton `Manager` handles domains' lifecycles and dependency injection (`Deps`).

Domains can communicate each other using `Event`s.

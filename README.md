# Cosmos DB Skill for Cursor

A comprehensive [Cursor](https://cursor.com) agent skill for managing Azure Cosmos DB resources — accounts, databases, containers, documents, queries, throughput, indexing, stored procedures, triggers, UDFs, and more.

## What's Included

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill instructions — account, database, container, document CRUD, throughput, queries |
| `reference.md` | Advanced operations — composite indexes, unique keys, TTL, stored procs, triggers, UDFs, backup/restore, RBAC, networking, monitoring, multi-region, SQL query reference |
| `scripts/cosmos-auth.py` | Helper script to generate Cosmos DB REST API HMAC-SHA256 authorization headers |
| `accounts.local.json` | **Local only (gitignored)** — stores saved Cosmos DB account URLs and keys for quick reuse |

## Installation

Copy or clone this folder into your Cursor skills directory:

```bash
# Personal (available across all projects)
git clone https://github.com/guyma-tr/cosmos-db-skill.git ~/.cursor/skills/cosmos-db-skill
```

## Prerequisites

- **Azure CLI** (`az`) — installed and logged in
- **Python 3** — for the auth helper script (document operations)

## Capabilities

- **Accounts** — list, show, create, delete, get keys/connection strings
- **Databases** — list, create, delete (with optional shared throughput)
- **Containers** — list, create, show, delete (with partition keys, TTL, unique keys, composite indexes, autoscale)
- **Documents** — create, read, replace, delete, query (via REST API with HMAC auth)
- **Queries** — full SQL query support including cross-partition, aggregations, JOINs, geospatial
- **Throughput** — read, update, migrate between manual and autoscale
- **Indexing** — view and update indexing policies (consistent, selective, spatial, composite, none)
- **Stored Procedures** — create, list, show, execute, delete
- **Triggers** — create pre/post triggers, list, show, delete
- **UDFs** — create, list, show, delete, use in queries
- **Backup & Restore** — check policy, point-in-time restore
- **Networking** — VNet rules, IP ranges, private endpoints
- **RBAC** — data-plane role definitions and assignments
- **Multi-Region** — add regions, enable multi-write, manual failover
- **Monitoring** — Azure Monitor metrics (RU/s, requests, storage)

## Cross-Platform

Works on both **bash** (macOS/Linux) and **PowerShell** (Windows). The skill auto-detects the shell and uses appropriate syntax.

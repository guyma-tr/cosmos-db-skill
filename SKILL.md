---
name: cosmos-db-skill
description: Manage Azure Cosmos DB accounts, databases, containers, documents, queries, indexing, throughput, stored procedures, and more using Azure CLI. Use when the user wants to create, read, update, delete, query, or manage Cosmos DB resources, documents, containers, databases, RU/s, indexes, stored procedures, triggers, or UDFs.
---

# Azure Cosmos DB Management

Manages Azure Cosmos DB resources using the Azure CLI (`az cosmosdb`).

## Cross-Platform Support

**IMPORTANT:** This skill runs on both macOS/Linux (bash) and Windows (PowerShell). At the start of every invocation, detect the user's OS and shell, then use the appropriate commands throughout.

- **Line continuation:** `\` on bash, `` ` `` (backtick) on PowerShell.
- **JSON quoting:** On bash, use single quotes for JSON bodies. On PowerShell, escape inner double quotes or use `@' ... '@` here-strings.

## Execution Policy

**Do NOT ask for confirmation before executing any operation.** When the user provides enough information, execute the command immediately and report the result. Only ask for values the user did not provide.

---

## Saved Accounts (Local Credentials Store)

The file `accounts.local.json` (in this skill's directory) stores known Cosmos DB account credentials locally so you don't need to look them up every time. **This file is gitignored and never pushed to GitHub.**

### File location

The file path is: `{this skill's directory}/accounts.local.json`

Resolve the skill directory from the SKILL.md path. For example if SKILL.md is at `~/.cursor/skills/cosmos-db-skill/SKILL.md`, then the file is at `~/.cursor/skills/cosmos-db-skill/accounts.local.json`.

### Format

```json
[
  {
    "alias": "my-service-int",
    "accountName": "int-my-cosmos-account",
    "resourceGroup": "int-infra-rg",
    "url": "https://int-my-cosmos-account.documents.azure.com/",
    "key": "<primary-master-key>",
    "region": "West Europe",
    "environment": "integration",
    "service": "my-service-name"
  }
]
```

Each entry has:

| Field | Required | Description |
|---|---|---|
| `alias` | Yes | Short unique name for quick lookup (e.g. `marketplace-int`, `payments-stg`) |
| `accountName` | Yes | Cosmos DB account name |
| `resourceGroup` | No | Azure resource group (saves a lookup for control-plane CLI commands) |
| `url` | Yes | Full Cosmos DB endpoint URL |
| `key` | Yes | Primary master key for REST API auth |
| `region` | No | Azure region |
| `environment` | No | Environment name (integration, staging, production) |
| `service` | No | Service/repo name this account belongs to |

### Lookup Behavior

**At the start of every operation**, before asking the user for account details:

1. **Read** `accounts.local.json` from this skill's directory.
2. **Match** the user's request against `alias`, `accountName`, `service`, or `environment` fields. Use fuzzy matching — e.g. if the user says "marketplace int", match an entry with `service: "marketplace-applications-api"` and `environment: "integration"`.
3. **If a match is found**, use the stored `url`, `key`, `resourceGroup`, and `accountName` directly — skip asking for these values.
4. **If no match is found**, proceed normally (ask the user or fetch from Azure CLI / Key Vault / etcd).
5. **Backfill missing fields**: If a match is found but some optional fields are missing (e.g. `resourceGroup`), and you discover them during the operation, update the entry in `accounts.local.json`.

### Adding New Accounts

When you successfully retrieve a new Cosmos DB account URL + key (from Key Vault, etcd, Azure CLI, or the user provides them), **automatically append** the entry to `accounts.local.json` so it's remembered for next time. Ask the user for a short alias, or generate one from `{service}-{environment}` (e.g. `marketplace-applications-api-int`).

### Listing Saved Accounts

When the user asks to list, show, or view saved accounts, read and display `accounts.local.json` as a table. **Never display the full key** — show only the first 8 characters followed by `...`.

---

## Prerequisites Check

**Run these checks automatically at the start of EVERY invocation, before doing anything else.**

### Step 1: Check Azure CLI

**bash:**
```bash
az version 2>/dev/null || echo "AZ_MISSING"
```

**PowerShell:**
```powershell
try { az version } catch { Write-Output "AZ_MISSING" }
```

**If missing, install:**
- **Windows:** `winget install --id Microsoft.AzureCLI --accept-source-agreements --accept-package-agreements`
- **macOS:** `brew install azure-cli`
- **Linux:** `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`

### Step 2: Check login

```bash
az account show --query "{name:name, id:id}" -o table 2>&1
```

If error → run `az login`, then verify again.

### Step 3: Check cosmosdb extension (only for NoSQL API data-plane operations)

Data-plane commands (`az cosmosdb sql container`, document operations via REST) are built-in. No extra extension is needed for most operations. If a command fails with "extension required", install:

```bash
az extension add --name cosmosdb-preview --yes
```

**Only proceed once all checks pass.**

---

## Inputs

Extract as much as possible from the user's message. Only ask for missing values.

| Field | When needed | Notes |
|---|---|---|
| **accountName** | All operations | Cosmos DB account name |
| **resourceGroup** | All control-plane ops | Azure resource group |
| **databaseName** | Database/container/document ops | SQL database name |
| **containerName** | Container/document ops | Container name |
| **partitionKeyPath** | Create container | e.g. `/id`, `/tenantId` |
| **documentId** | Document read/update/delete | The document `id` |
| **partitionKeyValue** | Document read/update/delete | Value for the partition key |
| **query** | Query operation | SQL query string |

---

## Account Operations

### List Accounts

```bash
az cosmosdb list --query "[].{Name:name, ResourceGroup:resourceGroup, Location:locations[0].locationName, Kind:kind}" -o table
```

### Show Account Details

```bash
az cosmosdb show --name {accountName} --resource-group {resourceGroup} -o json
```

### Create Account

```bash
az cosmosdb create --name {accountName} --resource-group {resourceGroup} --locations regionName={region} failoverPriority=0 isZoneRedundant=false --default-consistency-level Session
```

### Delete Account

```bash
az cosmosdb delete --name {accountName} --resource-group {resourceGroup} --yes
```

### List Connection Strings

```bash
az cosmosdb keys list --name {accountName} --resource-group {resourceGroup} --type connection-strings -o table
```

### List Keys

```bash
az cosmosdb keys list --name {accountName} --resource-group {resourceGroup} -o table
```

---

## Database Operations

### List Databases

```bash
az cosmosdb sql database list --account-name {accountName} --resource-group {resourceGroup} --query "[].{Name:name, Id:id}" -o table
```

### Create Database

Without shared throughput:
```bash
az cosmosdb sql database create --account-name {accountName} --resource-group {resourceGroup} --name {databaseName}
```

With shared throughput:
```bash
az cosmosdb sql database create --account-name {accountName} --resource-group {resourceGroup} --name {databaseName} --throughput {RUs}
```

### Delete Database

```bash
az cosmosdb sql database delete --account-name {accountName} --resource-group {resourceGroup} --name {databaseName} --yes
```

---

## Container Operations

### List Containers

```bash
az cosmosdb sql container list --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --query "[].{Name:name, PartitionKey:resource.partitionKey.paths[0], IndexingMode:resource.indexingPolicy.indexingMode}" -o table
```

### Create Container

```bash
az cosmosdb sql container create --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --partition-key-path {partitionKeyPath} --throughput {RUs}
```

With autoscale:
```bash
az cosmosdb sql container create --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --partition-key-path {partitionKeyPath} --max-throughput {maxRUs}
```

With composite indexes, unique keys, or TTL — see [reference.md](reference.md).

### Show Container Details

```bash
az cosmosdb sql container show --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} -o json
```

### Delete Container

```bash
az cosmosdb sql container delete --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --yes
```

---

## Document Operations (Data-Plane via REST API)

Azure CLI does not have built-in document-level CRUD commands. Use the Cosmos DB REST API with a master key for document operations.

### Getting the Key

**Preferred:** Look up the account in `accounts.local.json` (see Saved Accounts above). Use the stored `key` and `url` directly.

**Fallback** (if not in saved accounts):

```bash
ACCOUNT_KEY=$(az cosmosdb keys list --name {accountName} --resource-group {resourceGroup} --query primaryMasterKey -o tsv)
```

**PowerShell:**
```powershell
$ACCOUNT_KEY = az cosmosdb keys list --name {accountName} --resource-group {resourceGroup} --query primaryMasterKey -o tsv
```

After retrieving a key via fallback, save it to `accounts.local.json` for future use.

### REST API Base URL

```
https://{accountName}.documents.azure.com
```

### Authorization Header Generation

Cosmos DB REST API requires an HMAC-SHA256 authorization token. Use the helper script at `scripts/cosmos-auth.py` to generate the auth headers:

**bash:**
```bash
python3 "$(dirname "$0")/scripts/cosmos-auth.py" --verb {verb} --resource-type {resourceType} --resource-link {resourceLink} --key "$ACCOUNT_KEY"
```

**PowerShell:**
```powershell
python "$PSScriptRoot/scripts/cosmos-auth.py" --verb {verb} --resource-type {resourceType} --resource-link {resourceLink} --key $ACCOUNT_KEY
```

The script prints `x-ms-date` and `authorization` header values. Use them in subsequent curl calls.

### Create Document

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb post --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X POST "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "Content-Type: application/json" \
  -H "x-ms-documentdb-partitionkey: [\"{partitionKeyValue}\"]" \
  -d '{jsonBody}'
```

### Read Document

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb get --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}/docs/{documentId}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs/{documentId}" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "x-ms-documentdb-partitionkey: [\"{partitionKeyValue}\"]"
```

### Replace (Update) Document

Uses HTTP PUT. The body must include the `id` field and all document properties (full replace):

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb put --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}/docs/{documentId}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X PUT "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs/{documentId}" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "Content-Type: application/json" \
  -H "x-ms-documentdb-partitionkey: [\"{partitionKeyValue}\"]" \
  -d '{fullJsonBody}'
```

### Delete Document

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb delete --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}/docs/{documentId}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X DELETE "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs/{documentId}" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "x-ms-documentdb-partitionkey: [\"{partitionKeyValue}\"]"
```

### Query Documents

**Simple queries (non-aggregate, or single-partition):**

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb post --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X POST "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "Content-Type: application/query+json" \
  -H "x-ms-documentdb-isquery: True" \
  -H "x-ms-documentdb-query-enablecrosspartition: True" \
  -d '{"query": "{sqlQuery}", "parameters": []}'
```

### Cross-Partition Aggregate Queries (COUNT, SUM, AVG, MIN, MAX, GROUP BY)

The Cosmos DB REST gateway **cannot directly execute** cross-partition aggregate queries. It returns a `BadRequest` with `additionalErrorInfo` containing a `rewrittenQuery` and partition range info. You must fan out the query yourself.

**Procedure:**

1. **Get partition key ranges** for the container:

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb get --resource-type pkranges --resource-link "dbs/{databaseName}/colls/{containerName}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/pkranges" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31"
```

Parse `PartitionKeyRanges[].id` from the response to get range IDs (e.g. `"0"`, `"1"`, ...).

2. **Use the rewritten query** from the gateway error, or rewrite manually:

| Original query | Rewritten query |
|---|---|
| `SELECT VALUE COUNT(1) FROM c` | `SELECT VALUE [{"item": COUNT(1)}] FROM c` |
| `SELECT COUNT(1) AS cnt FROM c` | `SELECT VALUE [{"item": COUNT(1)}] FROM c` |
| `SELECT VALUE SUM(c.amount) FROM c` | `SELECT VALUE [{"item": SUM(c.amount)}] FROM c` |

3. **Execute the rewritten query against each partition range** using the `x-ms-documentdb-partitionkeyrangeid` header instead of the cross-partition header:

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb post --resource-type docs --resource-link "dbs/{databaseName}/colls/{containerName}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X POST "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/docs" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "Content-Type: application/query+json" \
  -H "x-ms-documentdb-isquery: True" \
  -H "x-ms-documentdb-partitionkeyrangeid: {rangeId}" \
  -d '{"query": "{rewrittenQuery}", "parameters": []}'
```

4. **Aggregate results** client-side: sum the `item` values across all partition ranges for COUNT/SUM, take min/max for MIN/MAX, compute weighted average for AVG.

**PowerShell note:** Write the query JSON to a temp file and use `@path` to avoid escaping issues:

```powershell
Set-Content -Path "$env:TEMP\cosmos-query.json" -Value '{"query": "SELECT VALUE [{\"item\": COUNT(1)}] FROM c", "parameters": []}' -Encoding UTF8
# then use -d "@$env:TEMP\cosmos-query.json" in the curl call
```

**C# / .NET note:** When building query JSON bodies in C#, **always use `JsonSerializer.Serialize`** — never use manual string interpolation with `$"{{...}}"`. The curly-brace escaping interacts badly with JSON and causes `SC1001: Syntax error, incorrect syntax near '{'` from Cosmos DB.

Correct:
```csharp
var queryBody = JsonSerializer.Serialize(new
{
    query = $"SELECT c.name FROM c WHERE c.id = {someId}",
    parameters = Array.Empty<object>()
});
request.Content = new StringContent(queryBody);
request.Content.Headers.ContentType = new MediaTypeHeaderValue("application/query+json");
```

Two common mistakes that both cause `SC1001: Syntax error, incorrect syntax near '{'`:

1. **Manual string interpolation** — use `JsonSerializer.Serialize` instead:
```csharp
// WRONG — curly brace escaping breaks JSON
var queryJson = $"{{\"query\":\"SELECT c.name FROM c WHERE c.id = {someId}\",\"parameters\":[]}}";
```

2. **`StringContent` with charset** — Cosmos DB rejects `application/query+json; charset=utf-8` and falls back to parsing the body as raw SQL:
```csharp
// WRONG — adds "; charset=utf-8" which breaks Cosmos
new StringContent(queryBody, Encoding.UTF8, "application/query+json");

// CORRECT — set Content-Type without charset
request.Content = new StringContent(queryBody);
request.Content.Headers.ContentType = new MediaTypeHeaderValue("application/query+json");
```

---

## Throughput Management

### Read Throughput

Container level:
```bash
az cosmosdb sql container throughput show --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} -o json
```

Database level:
```bash
az cosmosdb sql database throughput show --account-name {accountName} --resource-group {resourceGroup} --name {databaseName} -o json
```

### Update Throughput (Manual)

```bash
az cosmosdb sql container throughput update --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --throughput {RUs}
```

### Migrate to Autoscale

```bash
az cosmosdb sql container throughput migrate --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --throughput-type autoscale
```

### Migrate to Manual

```bash
az cosmosdb sql container throughput migrate --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --throughput-type manual
```

---

## Stored Procedures, Triggers & UDFs

See [reference.md](reference.md) for full details on creating and executing stored procedures, triggers, and UDFs.

### Quick Reference

| Operation | Command |
|---|---|
| List stored procs | `az cosmosdb sql stored-procedure list ...` |
| Create stored proc | `az cosmosdb sql stored-procedure create --body @sproc.js ...` |
| Execute stored proc | REST API POST to `sprocs/{sprocId}` |
| Create trigger | `az cosmosdb sql trigger create --body @trigger.js --type {Pre\|Post} --operation {All\|Create\|Replace\|Delete} ...` |
| Create UDF | `az cosmosdb sql user-defined-function create --body @udf.js ...` |

---

## Indexing Policy

### Show Current Policy

```bash
az cosmosdb sql container show --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --query resource.indexingPolicy -o json
```

### Update Indexing Policy

```bash
az cosmosdb sql container update --account-name {accountName} --resource-group {resourceGroup} --database-name {databaseName} --name {containerName} --idx @indexing-policy.json
```

See [reference.md](reference.md) for indexing policy JSON examples.

---

## Error Handling

| Error | Action |
|---|---|
| `ResourceNotFound` | Verify account/database/container names |
| `Forbidden` / `403` | Check RBAC or key permissions |
| `Request rate is large` (429) | Throughput exceeded — increase RU/s or retry |
| `Entity with specified id already exists` (409) | Document/resource already exists — use replace instead |
| `Request size is too large` (413) | Document exceeds 2 MB limit — reduce size |
| `az: command not found` | Azure CLI not installed — run install step |
| `Please run 'az login'` | Not logged in — run `az login` |
| HMAC auth errors | Regenerate auth headers; check key is correct |

---

## Quick Reference

| Operation | Command Pattern |
|---|---|
| List accounts | `az cosmosdb list` |
| Get keys | `az cosmosdb keys list` |
| List databases | `az cosmosdb sql database list` |
| Create database | `az cosmosdb sql database create` |
| List containers | `az cosmosdb sql container list` |
| Create container | `az cosmosdb sql container create --partition-key-path ...` |
| Show indexing | `az cosmosdb sql container show --query resource.indexingPolicy` |
| Read throughput | `az cosmosdb sql container throughput show` |
| Update throughput | `az cosmosdb sql container throughput update --throughput {RUs}` |
| CRUD documents | REST API via `https://{account}.documents.azure.com/...` |
| Query documents | REST API POST with `Content-Type: application/query+json` |
| Stored procedures | `az cosmosdb sql stored-procedure create/list/show/delete` |
| Triggers | `az cosmosdb sql trigger create/list/show/delete` |
| UDFs | `az cosmosdb sql user-defined-function create/list/show/delete` |

For advanced operations (composite indexes, unique keys, TTL, change feed, conflict resolution, backups, RBAC, networking), see [reference.md](reference.md).

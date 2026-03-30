# Cosmos DB Reference — Advanced Operations

## Container Creation — Advanced Options

### With TTL (Time-to-Live)

Default TTL on container (seconds). Documents without their own `ttl` field expire after this duration:

```bash
az cosmosdb sql container create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --name {containerName} \
  --partition-key-path {partitionKeyPath} \
  --throughput 400 \
  --default-ttl 86400
```

Set `--default-ttl -1` to enable TTL per-document (no container-level default). Set `--default-ttl 0` or omit to disable TTL.

### With Unique Keys

Unique key constraints enforce uniqueness within a logical partition:

```bash
az cosmosdb sql container create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --name {containerName} \
  --partition-key-path /tenantId \
  --unique-key-policy '{"uniqueKeys": [{"paths": ["/email"]}, {"paths": ["/username"]}]}'
```

### With Composite Indexes

Composite indexes improve ORDER BY on multiple fields:

```bash
az cosmosdb sql container create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --name {containerName} \
  --partition-key-path /tenantId \
  --idx @composite-index-policy.json
```

**composite-index-policy.json:**
```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [{"path": "/*"}],
  "excludedPaths": [{"path": "/\"_etag\"/?"}],
  "compositeIndexes": [
    [
      {"path": "/name", "order": "ascending"},
      {"path": "/timestamp", "order": "descending"}
    ]
  ]
}
```

### Hierarchical Partition Keys

For sub-partitioning (multi-level partition keys):

```bash
az cosmosdb sql container create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --name {containerName} \
  --partition-key-path /tenantId /userId /sessionId \
  --throughput 400
```

### With Conflict Resolution Policy

For multi-region write accounts:

```bash
az cosmosdb sql container create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --name {containerName} \
  --partition-key-path /id \
  --conflict-resolution-policy '{"mode": "LastWriterWins", "conflictResolutionPath": "/_ts"}'
```

---

## Indexing Policy Examples

### Consistent Indexing (Default)

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [{"path": "/*"}],
  "excludedPaths": [{"path": "/\"_etag\"/?"}]
}
```

### Selective Indexing (Reduce RU Cost)

Only index fields you actually query on:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {"path": "/name/?"},
    {"path": "/email/?"},
    {"path": "/status/?"}
  ],
  "excludedPaths": [{"path": "/*"}]
}
```

### Spatial Indexes

For GeoJSON geometry queries:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [{"path": "/*"}],
  "excludedPaths": [{"path": "/\"_etag\"/?"}],
  "spatialIndexes": [
    {"path": "/location/*", "types": ["Point", "Polygon", "LineString"]}
  ]
}
```

### No Indexing (Maximum Write Throughput)

```json
{
  "indexingMode": "none",
  "automatic": false
}
```

---

## Stored Procedures

### Create

```bash
az cosmosdb sql stored-procedure create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {sprocName} \
  --body @sproc.js
```

**Example sproc.js — bulk delete:**
```javascript
function bulkDelete(query) {
    var context = getContext();
    var container = context.getCollection();
    var response = context.getResponse();
    var deleted = 0;

    var accepted = container.queryDocuments(
        container.getSelfLink(), query,
        function (err, docs) {
            if (err) throw err;
            if (docs.length === 0) { response.setBody({ deleted: deleted }); return; }
            docs.forEach(function (doc) {
                container.deleteDocument(doc._self, function (err) {
                    if (err) throw err;
                    deleted++;
                });
            });
            response.setBody({ deleted: deleted });
        }
    );
    if (!accepted) throw new Error("Query was not accepted by the server.");
}
```

### List

```bash
az cosmosdb sql stored-procedure list \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --query "[].{Name:name}" -o table
```

### Show

```bash
az cosmosdb sql stored-procedure show \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {sprocName} -o json
```

### Execute (REST API)

```bash
AUTH=$(python3 scripts/cosmos-auth.py --verb post --resource-type sprocs \
  --resource-link "dbs/{databaseName}/colls/{containerName}/sprocs/{sprocName}" --key "$ACCOUNT_KEY")
DATE=$(echo "$AUTH" | head -1)
TOKEN=$(echo "$AUTH" | tail -1)

curl -s -X POST \
  "https://{accountName}.documents.azure.com/dbs/{databaseName}/colls/{containerName}/sprocs/{sprocName}" \
  -H "Authorization: $TOKEN" \
  -H "x-ms-date: $DATE" \
  -H "x-ms-version: 2018-12-31" \
  -H "Content-Type: application/json" \
  -H "x-ms-documentdb-partitionkey: [\"{partitionKeyValue}\"]" \
  -d '["{arg1}", "{arg2}"]'
```

### Delete

```bash
az cosmosdb sql stored-procedure delete \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {sprocName} --yes
```

---

## Triggers

### Create Pre-Trigger

Runs before the operation:

```bash
az cosmosdb sql trigger create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {triggerName} \
  --body @trigger.js \
  --type Pre \
  --operation Create
```

**Example trigger.js — auto-timestamp:**
```javascript
function addTimestamp() {
    var context = getContext();
    var request = context.getRequest();
    var doc = request.getBody();
    doc.createdAt = new Date().toISOString();
    doc.updatedAt = doc.createdAt;
    request.setBody(doc);
}
```

### Create Post-Trigger

Runs after the operation:

```bash
az cosmosdb sql trigger create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {triggerName} \
  --body @post-trigger.js \
  --type Post \
  --operation All
```

### List / Show / Delete Triggers

```bash
az cosmosdb sql trigger list --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} -o table
az cosmosdb sql trigger show --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} --name {n}
az cosmosdb sql trigger delete --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} --name {n} --yes
```

---

## User-Defined Functions (UDFs)

### Create UDF

```bash
az cosmosdb sql user-defined-function create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --database-name {databaseName} --container-name {containerName} \
  --name {udfName} \
  --body @udf.js
```

**Example udf.js — format currency:**
```javascript
function formatCurrency(amount) {
    return "$" + amount.toFixed(2);
}
```

**Usage in query:**
```sql
SELECT c.name, udf.formatCurrency(c.price) AS formattedPrice FROM c
```

### List / Show / Delete UDFs

```bash
az cosmosdb sql user-defined-function list --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} -o table
az cosmosdb sql user-defined-function show --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} --name {n}
az cosmosdb sql user-defined-function delete --account-name {a} --resource-group {rg} --database-name {db} --container-name {c} --name {n} --yes
```

---

## Backup & Restore

### Check Backup Policy

```bash
az cosmosdb show --name {accountName} --resource-group {resourceGroup} --query backupPolicy -o json
```

### Restore (Continuous Backup)

Point-in-time restore to a new account:

```bash
az cosmosdb restore --account-name {newAccountName} --resource-group {resourceGroup} \
  --target-database-account-name {sourceAccountName} \
  --restore-timestamp "{ISO8601Timestamp}" \
  --location "{region}" \
  --databases-to-restore name={databaseName} collections={containerName1} {containerName2}
```

---

## Networking

### Add Virtual Network Rule

```bash
az cosmosdb network-rule add --name {accountName} --resource-group {resourceGroup} \
  --vnet-name {vnetName} --subnet {subnetName}
```

### Add IP Range

```bash
az cosmosdb update --name {accountName} --resource-group {resourceGroup} \
  --ip-range-filter "{ip1},{ip2}"
```

### Enable Private Endpoint

```bash
az network private-endpoint create \
  --name {endpointName} --resource-group {resourceGroup} \
  --vnet-name {vnetName} --subnet {subnetName} \
  --private-connection-resource-id $(az cosmosdb show -n {accountName} -g {resourceGroup} --query id -o tsv) \
  --group-id Sql --connection-name {connectionName}
```

---

## RBAC (Data-Plane Role Assignments)

### List Built-in Roles

```bash
az cosmosdb sql role definition list --account-name {accountName} --resource-group {resourceGroup} -o table
```

### Create Role Assignment

```bash
az cosmosdb sql role assignment create \
  --account-name {accountName} --resource-group {resourceGroup} \
  --role-definition-id {roleDefinitionId} \
  --principal-id {aadObjectId} \
  --scope "/dbs/{databaseName}"
```

### List Role Assignments

```bash
az cosmosdb sql role assignment list --account-name {accountName} --resource-group {resourceGroup} -o table
```

---

## Change Feed

Change feed is consumed programmatically (SDK), not via CLI. To monitor changes:

1. **Azure Functions Cosmos DB Trigger** — recommended for event-driven processing.
2. **Change Feed Processor** (SDK) — for custom consumption logic.
3. **Change Feed Estimator** (SDK) — to monitor lag.

To check if change feed is enabled (it's always on for SQL API):

```bash
az cosmosdb sql container show --account-name {a} --resource-group {rg} --database-name {db} --name {c} \
  --query "{ChangeFeedPolicy: resource.changeFeedPolicy}" -o json
```

---

## Multi-Region

### Add a Region

```bash
az cosmosdb update --name {accountName} --resource-group {resourceGroup} \
  --locations regionName={primaryRegion} failoverPriority=0 \
  --locations regionName={secondaryRegion} failoverPriority=1
```

### Enable Multi-Region Writes

```bash
az cosmosdb update --name {accountName} --resource-group {resourceGroup} \
  --enable-multiple-write-locations true
```

### Manual Failover

```bash
az cosmosdb failover-priority-change --name {accountName} --resource-group {resourceGroup} \
  --failover-policies "{newPrimaryRegion}=0" "{oldPrimaryRegion}=1"
```

---

## Monitoring

### Show Metrics (via Azure Monitor)

```bash
az monitor metrics list --resource $(az cosmosdb show -n {accountName} -g {resourceGroup} --query id -o tsv) \
  --metric "TotalRequestUnits" --interval PT5M --aggregation Total -o table
```

Common metrics: `TotalRequestUnits`, `TotalRequests`, `DocumentCount`, `DataUsage`, `IndexUsage`, `ProvisionedThroughput`, `AvailableStorage`.

---

## Cosmos DB SQL Query Reference

### Basic Queries
```sql
SELECT * FROM c
SELECT c.id, c.name FROM c WHERE c.status = "active"
SELECT TOP 10 * FROM c ORDER BY c._ts DESC
SELECT VALUE COUNT(1) FROM c
```

### Filtering
```sql
SELECT * FROM c WHERE c.age > 25 AND c.city = "London"
SELECT * FROM c WHERE c.status IN ("active", "pending")
SELECT * FROM c WHERE IS_DEFINED(c.email)
SELECT * FROM c WHERE CONTAINS(c.name, "john", true)
SELECT * FROM c WHERE STARTSWITH(c.name, "J")
SELECT * FROM c WHERE ARRAY_CONTAINS(c.tags, "premium")
```

### Aggregations
```sql
SELECT c.city, COUNT(1) AS count, AVG(c.age) AS avgAge FROM c GROUP BY c.city
SELECT VALUE MAX(c.price) FROM c
SELECT VALUE SUM(c.quantity) FROM c WHERE c.category = "electronics"
```

### JOINs (within a document)
```sql
SELECT c.id, t AS tag FROM c JOIN t IN c.tags WHERE t = "urgent"
```

### Subqueries
```sql
SELECT * FROM c WHERE c.id IN (SELECT VALUE r.orderId FROM r IN c.recentOrders WHERE r.total > 100)
```

### Pagination
Use `OFFSET ... LIMIT` for pagination:
```sql
SELECT * FROM c ORDER BY c.createdAt DESC OFFSET 20 LIMIT 10
```

### Geospatial
```sql
SELECT * FROM c WHERE ST_DISTANCE(c.location, {"type": "Point", "coordinates": [-73.97, 40.77]}) < 5000
```

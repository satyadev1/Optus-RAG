# Milvus Offline Database Setup

This project contains a fully offline Milvus vector database configuration.

## Features
- **Completely Offline**: Network configured with `internal: true` to prevent internet access
- **Standalone Mode**: Single-node deployment for simplicity
- **Persistent Storage**: All data stored locally in `./volumes/`
- **No Version Checks**: Disabled external version checking

## Prerequisites
- Docker and Docker Compose installed
- At least 4GB of RAM available
- 10GB of disk space

## Quick Start

### 1. Start Milvus (Offline)
```bash
docker-compose up -d
```

### 2. Check Status
```bash
docker-compose ps
```

All three services should show "healthy":
- `milvus-standalone` (port 19530)
- `milvus-etcd` (metadata storage)
- `milvus-minio` (object storage)

### 3. Stop Milvus
```bash
docker-compose down
```

### 4. Stop and Remove All Data
```bash
docker-compose down -v
rm -rf volumes/
```

## Access Points
- **Milvus**: `localhost:19530` (gRPC API)
- **MinIO Console**: `http://localhost:9001` (minioadmin/minioadmin)
- **Milvus Metrics**: `http://localhost:9091/metrics`

## Python Client Example

Install the Python SDK:
```bash
pip install pymilvus
```

Then use `example.py` to test the connection and basic operations.

## Offline Configuration Details

The setup is configured for complete offline operation:
1. Docker network set to `internal: true` - blocks external internet
2. Version checking disabled via `MILVUS_CHECK_VERSION: "false"`
3. All dependencies (etcd, minio) run locally
4. Data persisted to local `./volumes/` directory

## Data Storage
All data is stored in:
- `./volumes/milvus/` - Vector data and indexes
- `./volumes/etcd/` - Metadata
- `./volumes/minio/` - Object storage

## Troubleshooting

**Containers not starting?**
```bash
docker-compose logs
```

**Reset everything?**
```bash
docker-compose down -v
rm -rf volumes/
docker-compose up -d
```

**Check connectivity?**
```bash
docker exec -it milvus-standalone curl http://localhost:9091/healthz
```

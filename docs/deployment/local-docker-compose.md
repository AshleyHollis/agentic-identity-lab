# Local Docker Compose

Run the Python services locally using Docker Compose. These files are placeholders and do not include secrets.

## Prerequisites
- Docker Desktop

## Single-tenant
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.single-tenant.yml up --build
```

## Vendor-shaped single-tenant
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.vendor-shaped.yml up --build
```

## Cross-tenant local
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.cross-tenant.local.yml up --build
```

## Notes
- Replace placeholder tenant IDs in the compose overrides.
- Service folders under `services/` are expected to be added later.

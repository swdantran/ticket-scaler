# Autoscaling Ticket Reservation Platform

A distributed ticket reservation backend designed for high-concurrency flash-sale traffic. Uses transactional reservations and idempotent requests to prevent overselling, Kafka for asynchronous processing, and Kubernetes autoscaling based on API load and queue backlog.

## Stack

- **API:** Python, FastAPI
- **Database:** PostgreSQL
- **Cache:** Redis
- **Messaging:** Kafka
- **Containers:** Docker
- **Orchestration:** Kubernetes
- **API Autoscaling:** Kubernetes HPA
- **Worker Autoscaling:** KEDA

## Project structure

```text
app/
  api/
    main.py
    routes/
      events.py
      reservations.py
    schemas.py

  db/
    models.py
    session.py

  services/
    reservation.py
    idempotency.py
    cache.py

  messaging/
    producer.py
    consumer.py
    handlers.py

  workers/
    reservation_worker.py

k8s/
  api-deployment.yaml
  api-service.yaml
  worker-deployment.yaml
  hpa.yaml
  keda-scaledobject.yaml

docker-compose.yml
requirements.txt
.env.example
```

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection URL |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address |
| `KAFKA_TOPIC` | Kafka reservation event topic |

### 3. Start infrastructure

```bash
docker compose up -d
```

This starts the local infrastructure required by the platform:

- PostgreSQL
- Redis
- Kafka

## Running

Start the API:

```bash
source .venv/bin/activate
uvicorn app.api.main:app --reload
```

The server runs on:

```text
http://localhost:8000
```

Start the Kafka worker:

```bash
python -m app.workers.reservation_worker
```

## API

### `GET /events`

Returns available ticketed events.

```bash
curl http://localhost:8000/events
```

### `GET /events/{event_id}`

Returns an event and its available seats.

```bash
curl http://localhost:8000/events/1
```

### `POST /reservations`

Attempts to reserve a seat.

```bash
curl -X POST http://localhost:8000/reservations \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: abc-123" \
  -d '{
    "event_id": 1,
    "seat_id": 42,
    "user_id": "user-123"
  }'
```

Example response:

```json
{
  "reservation_id": 491,
  "seat_id": 42,
  "status": "reserved"
}
```

Repeated requests using the same idempotency key return the existing reservation instead of creating a duplicate.

## Reservation pipeline

| Stage | Component | Description |
| --- | --- | --- |
| 1 | `reservations.py` | Receive reservation request |
| 2 | `idempotency.py` | Check whether the request was already processed |
| 3 | `reservation.py` | Begin a database transaction and lock the requested seat |
| 4 | PostgreSQL | Atomically update seat state and create the reservation |
| 5 | `producer.py` | Publish the successful reservation event to Kafka |
| 6 | `consumer.py` | Consume and process the event asynchronously |
| 7 | Worker | Commit the Kafka offset after successful processing |

## Concurrency control

Seat reservations use PostgreSQL transactions and row-level locking to prevent multiple clients from successfully reserving the same seat.

Conceptually:

```sql
BEGIN;

SELECT *
FROM seats
WHERE id = $1
FOR UPDATE;

UPDATE seats
SET status = 'reserved'
WHERE id = $1;

INSERT INTO reservations (...);

COMMIT;
```

The row lock serializes concurrent reservation attempts against the same seat and keeps PostgreSQL as the source of truth for ticket inventory.

## Idempotency

Clients can safely retry reservation requests using an `Idempotency-Key`.

```text
request #1 -> abc-123 -> reservation 491
request #2 -> abc-123 -> reservation 491
```

This prevents duplicate purchases caused by network retries or repeated client requests.

## Event processing

Successful reservations are published to Kafka so asynchronous work can be processed independently from the main HTTP request path.

```text
POST /reservations
        |
        v
   PostgreSQL
        |
        v
      Kafka
        |
   +----+----+
   |         |
 worker    worker
```

Consumers process reservation events independently and can retry failed work after transient failures.

## Autoscaling

The API and asynchronous workers scale independently based on different workload signals.

### Kubernetes HPA

The Horizontal Pod Autoscaler scales FastAPI replicas as API load increases.

```text
request traffic increases
          |
          v
API resource usage increases
          |
          v
         HPA
          |
          v
API replicas increase
```

### KEDA

KEDA scales Kafka consumers based on queue backlog.

```text
Kafka backlog increases
        |
        v
       KEDA
        |
        v
worker replicas increase
        |
        v
backlog decreases
```

This allows the worker pool to scale based on pending work instead of relying only on CPU utilization.

## Kubernetes

Deploy the application:

```bash
kubectl apply -f k8s/
```

Inspect running workloads:

```bash
kubectl get pods
kubectl get deployments
```

Inspect API autoscaling:

```bash
kubectl get hpa
```

Inspect KEDA resources:

```bash
kubectl get scaledobjects
```

## Reliability properties

The system is designed around several core guarantees:

```text
A seat cannot have multiple successful reservations.

Retrying the same logical request does not create another reservation.

Kafka events can be retried after temporary consumer failures.

API capacity scales independently from worker capacity.

Worker capacity increases as Kafka backlog grows.
```

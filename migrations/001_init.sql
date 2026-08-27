BEGIN;

CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    venue TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE seats (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    seat_number TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),

    status TEXT NOT NULL DEFAULT 'AVAILABLE'
        CHECK (status IN ('AVAILABLE', 'RESERVED', 'PURCHASED')),

    reserved_by TEXT,
    reservation_expires_at TIMESTAMPTZ,

    UNIQUE(event_id, section, seat_number)
);

CREATE TABLE reservations (
    id UUID PRIMARY KEY,
    seat_id BIGINT NOT NULL REFERENCES seats(id),
    user_id TEXT NOT NULL,

    status TEXT NOT NULL
        CHECK (status IN ('ACTIVE', 'EXPIRED', 'COMPLETED')),

    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    reservation_id UUID NOT NULL REFERENCES reservations(id),

    idempotency_key TEXT NOT NULL UNIQUE,

    status TEXT NOT NULL
        CHECK (status IN ('PENDING', 'CONFIRMED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seats_event_status
    ON seats(event_id, status);

CREATE INDEX idx_reservations_expires_at
    ON reservations(expires_at);

COMMIT;
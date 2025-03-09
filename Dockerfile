# Stage 1: Build Frontend (Chat UI)
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY chat-ui/ .
RUN npm install
RUN npm run build

# Stage 2: Build Frontend (StreetCred UI)
FROM node:18-alpine AS streetcred-builder
WORKDIR /streetcred
COPY streetcredui/ .
RUN npm install --legacy-peer-deps
RUN npm run build

# Stage 3: Build Backend
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-builder
ADD . /flare-ai-defai
WORKDIR /flare-ai-defai
RUN uv sync --frozen

# Stage 4: Final Image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install nginx, supervisor, nodejs, and Caddy
RUN apt-get update && \
    apt-get install -y nginx supervisor curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs caddy && \
    rm -rf /var/lib/apt/lists/*

# Copy SSL certificates for backend
COPY cert.pem /app/cert.pem
COPY key.pem /app/key.pem

# Copy SSL certificates for Caddy
COPY cert.pem /etc/caddy/cert.pem
COPY key.pem /etc/caddy/key.pem

WORKDIR /app

# Copy backend files
COPY --from=backend-builder /flare-ai-defai/.venv ./.venv
COPY --from=backend-builder /flare-ai-defai/src ./src
COPY --from=backend-builder /flare-ai-defai/pyproject.toml .
COPY --from=backend-builder /flare-ai-defai/README.md .

# Copy Flare AI backend files
COPY src/flare_ai_defai /app/flare_ai_defai
COPY pyproject.toml /app/

# Copy chat-ui frontend files
COPY --from=frontend-builder /frontend/build /usr/share/nginx/html

# Copy streetcredui files
COPY --from=streetcred-builder /streetcred /app/streetcredui

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-enabled/default

# Copy Caddyfile
COPY Caddyfile /etc/caddy/Caddyfile

# Setup supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Allow workload operator to override environment variables
LABEL "tee.launch_policy.allow_env_override"="GEMINI_API_KEY,GEMINI_MODEL,WEB3_PROVIDER_URL,WEB3_EXPLORER_URL,SIMULATE_ATTESTATION,PLAID_CLIENT_ID,PLAID_SECRET,PLAID_ENV"
LABEL "tee.launch_policy.log_redirect"="always"

EXPOSE 80 3000 8080

# Start supervisor (which will start nginx, backend, streetcredui, and flare-ai)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
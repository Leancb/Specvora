FROM python:3.12-slim

RUN apt-get update \
    && apt-get install --yes --no-install-recommends nftables util-linux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/specvora
COPY . .
RUN python -m pip install --no-cache-dir ".[dev]" \
    && chmod 0555 /opt/specvora/deploy/egress/entrypoint.sh

ENTRYPOINT ["/opt/specvora/deploy/egress/entrypoint.sh"]
CMD ["python", "-m", "pytest", "--help"]

FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY config ./config
COPY src ./src

RUN pip install --no-cache-dir -e ".[dev]"

ENV FBE_DEMO=1
ENV FBE_PORT=8090

EXPOSE 8090
CMD ["fly-brain-engine", "--host", "0.0.0.0", "--port", "8090", "--demo"]

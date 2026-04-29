FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Build-time metadata
ARG BUILD_TIMESTAMP=unknown
ARG BUILD_VERSION=unknown
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}
ENV BUILD_VERSION=${BUILD_VERSION}

EXPOSE 8000

ENV UNIFI_API_KEY=""
ENV UNIFI_GATEWAY_HOST="api.ui.com"
ENV UNIFI_GATEWAY_PORT="443"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"

CMD ["python", "main.py"]
FROM python:3.12-slim

WORKDIR /app

# Install dependencies without uv for a simpler, leaner image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# MCP SSE server listens on this port
EXPOSE 8000

ENV UNIFI_API_KEY=""
ENV UNIFI_GATEWAY_HOST="192.168.1.1"
ENV UNIFI_GATEWAY_PORT="443"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"

CMD ["python", "main.py"]

# Travel Planner

FastAPI and CrewAI travel planner using an Ollama model running on the host
machine.

## Run with Docker

### Prerequisites

- Docker Desktop
- Ollama installed on the host machine
- The `qwen2.5:7b` Ollama model
- Travel-provider API keys in `app/.env`

If `app/.env` does not exist, copy `app/.env.example` to `app/.env` and fill in
the API keys. Do not commit `app/.env`.

### 1. Make Ollama accessible to Docker

The API runs in a container, but Ollama runs on the host. Ollama must therefore
listen on an address that Docker can reach.

In PowerShell, stop any already-running Ollama server, then start it with:

```powershell
$env:OLLAMA_HOST = "0.0.0.0:11434"
ollama serve
```

In a separate terminal, make sure the model is available:

```powershell
ollama pull qwen2.5:7b
```

Only expose port `11434` on trusted networks. The application container reaches
it through `http://host.docker.internal:11434`.

### 2. Start the application

From the repository root:

```powershell
docker compose up --build
```

Open <http://localhost:8000>. The health endpoint is available at
<http://localhost:8000/api/health>.

To run in the background:

```powershell
docker compose up --build -d
```

View logs or stop the application with:

```powershell
docker compose logs -f travel-planner
docker compose down
```

To use a different browser-facing port:

```powershell
$env:APP_PORT = "8080"
docker compose up --build
```

Then open <http://localhost:8080>.

## What Compose runs

Compose runs only the FastAPI/CrewAI application. It injects the values from
`app/.env`, overrides `OLLAMA_HOST` for container-to-host communication, and
publishes the API on port `8000`. Ollama and its model data remain outside
Docker.

Changing Python source code requires rebuilding the image:

```powershell
docker compose up --build
```

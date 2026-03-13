---
name: container-manager
description: Use this skill when the user wants to manage Docker containers, build images, inspect logs, handle Docker Compose, or work with container orchestration.
---

# Container Manager

## Overview

Full Docker lifecycle management via the Python SDK and CLI. List, start, stop, build, inspect, stream logs, and manage Docker Compose stacks.

## Connect to Docker

```python
import docker

client = docker.from_env()  # uses DOCKER_HOST or default socket
# or explicitly:
client = docker.DockerClient(base_url="unix://var/run/docker.sock")
```

## Container Operations

```python
def list_containers(all_containers: bool = False) -> list[dict]:
    containers = client.containers.list(all=all_containers)
    return [{"id": c.short_id, "name": c.name, "status": c.status,
             "image": c.image.tags[0] if c.image.tags else c.image.short_id}
            for c in containers]

def start_container(name_or_id: str) -> str:
    c = client.containers.get(name_or_id)
    c.start()
    return f"Started {c.name}"

def stop_container(name_or_id: str, timeout: int = 10) -> str:
    c = client.containers.get(name_or_id)
    c.stop(timeout=timeout)
    return f"Stopped {c.name}"

def restart_container(name_or_id: str) -> str:
    c = client.containers.get(name_or_id)
    c.restart()
    return f"Restarted {c.name}"

def remove_container(name_or_id: str, force: bool = False) -> str:
    c = client.containers.get(name_or_id)
    c.remove(force=force)
    return f"Removed {name_or_id}"
```

## Streaming Logs

```python
def stream_logs(name_or_id: str, tail: int = 50) -> None:
    c = client.containers.get(name_or_id)
    for line in c.logs(stream=True, tail=tail, follow=True):
        print(line.decode().rstrip())

def get_recent_logs(name_or_id: str, tail: int = 100) -> str:
    c = client.containers.get(name_or_id)
    return c.logs(tail=tail).decode()
```

## Build Images

```python
def build_image(path: str, tag: str, buildargs: dict | None = None) -> str:
    image, logs = client.images.build(
        path=path, tag=tag, buildargs=buildargs or {}, rm=True
    )
    for log in logs:
        if "stream" in log:
            print(log["stream"].rstrip())
    return image.tags[0]
```

## Container Stats / Health

```python
def get_stats(name_or_id: str) -> dict:
    c = client.containers.get(name_or_id)
    stats = c.stats(stream=False)
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                stats["precpu_stats"]["cpu_usage"]["total_usage"]
    sys_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                stats["precpu_stats"]["system_cpu_usage"]
    cpu_pct = (cpu_delta / sys_delta) * 100 if sys_delta else 0
    mem = stats["memory_stats"]
    mem_mb = mem.get("usage", 0) / 1024 / 1024
    return {"name": c.name, "cpu_pct": round(cpu_pct, 2), "mem_mb": round(mem_mb, 1)}
```

## Docker Compose (via CLI)

```python
import subprocess

def compose_up(project_dir: str, detach: bool = True) -> str:
    cmd = ["docker", "compose", "up"]
    if detach:
        cmd.append("-d")
    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    return result.stdout + result.stderr

def compose_down(project_dir: str, volumes: bool = False) -> str:
    cmd = ["docker", "compose", "down"]
    if volumes:
        cmd.append("-v")
    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    return result.stdout + result.stderr

def compose_logs(project_dir: str, service: str | None = None, tail: int = 50) -> str:
    cmd = ["docker", "compose", "logs", f"--tail={tail}"]
    if service:
        cmd.append(service)
    result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
    return result.stdout
```

## Exec Into Container

```python
def exec_command(name_or_id: str, command: list[str]) -> str:
    c = client.containers.get(name_or_id)
    exit_code, output = c.exec_run(command)
    return output.decode()

# Example: check nginx config
# exec_command("nginx", ["nginx", "-t"])
```

## Quick Reference

| Task | Method | Notes |
|------|--------|-------|
| List containers | `client.containers.list()` | `all=True` for stopped |
| Start/stop | `.start()` / `.stop()` | timeout param for stop |
| Stream logs | `.logs(stream=True)` | yields bytes |
| Build image | `client.images.build()` | returns (Image, logs) |
| Compose up | `docker compose up -d` | via subprocess |
| Stats | `.stats(stream=False)` | CPU%, memory |
| Exec | `.exec_run(cmd)` | returns (exit_code, output) |

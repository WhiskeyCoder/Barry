"""
HTTP client for fly-brain-engine experiment scripts.
"""

from __future__ import annotations

from typing import Any

import httpx


class EngineClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8090", timeout: float = 300.0) -> None:
        if not base_url.startswith("http"):
            base_url = f"http://{base_url}"
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def health(self) -> dict:
        r = self._http.get("/health")
        r.raise_for_status()
        return r.json()

    def capabilities(self) -> dict:
        r = self._http.get("/v1/capabilities")
        r.raise_for_status()
        return r.json()

    def create_brain(
        self,
        name: str,
        *,
        connectome: str | None = None,
        scale: str = "mini",
        seed: int = 42,
    ) -> str:
        payload: dict[str, Any] = {"name": name, "scale": scale, "seed": seed}
        if connectome:
            payload["connectome"] = connectome
        r = self._http.post("/v1/brains", json=payload)
        r.raise_for_status()
        return r.json()["id"]

    def create_multiverse(
        self,
        name: str,
        count: int = 10,
        *,
        connectome: str | None = "procedural",
        scale: str = "mini",
        seed: int = 42,
        variants: list[dict[str, Any]] | None = None,
    ) -> dict:
        r = self._http.post(
            "/v1/experiments/multiverse",
            json={
                "name": name,
                "count": count,
                "connectome": connectome,
                "scale": scale,
                "seed": seed,
                "variants": variants,
            },
        )
        r.raise_for_status()
        return r.json()

    def step_multiverse(self, ensemble_id: str, milliseconds: float = 10.0) -> dict:
        r = self._http.post(
            f"/v1/experiments/multiverse/{ensemble_id}/step",
            params={"milliseconds": milliseconds},
        )
        r.raise_for_status()
        return r.json()

    def inject(
        self,
        brain_id: str,
        channel: str,
        data: Any,
        step_ms: float = 10.0,
    ) -> dict:
        r = self._http.post(
            "/v1/experiments/inject",
            json={
                "brain_id": brain_id,
                "channel": channel,
                "data": data,
                "step_ms": step_ms,
            },
        )
        r.raise_for_status()
        return r.json()

    def step(self, brain_id: str, milliseconds: float = 10.0) -> dict:
        r = self._http.post(f"/v1/brains/{brain_id}/step", params={"milliseconds": milliseconds})
        r.raise_for_status()
        return r.json()

    def snapshot(self, brain_id: str) -> dict:
        r = self._http.get(f"/v1/brains/{brain_id}/snapshot")
        r.raise_for_status()
        return r.json()

    def create_session(self, name: str, brain_id: str, dimension: int = 2) -> dict:
        r = self._http.post(
            "/v1/experiments/sessions",
            json={"name": name, "brain_id": brain_id, "dimension": dimension},
        )
        r.raise_for_status()
        return r.json()

    def session_step(self, session_id: str, milliseconds: float = 10.0) -> dict:
        r = self._http.post(
            f"/v1/experiments/sessions/{session_id}/step",
            params={"milliseconds": milliseconds},
        )
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._http.close()

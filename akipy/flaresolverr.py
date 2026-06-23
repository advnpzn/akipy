import httpx


class FlareSolverrError(Exception):
    pass


class FlareSolverrClient:
    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def _build_payload(
        self, cmd: str, url: str, max_timeout: int = 60000, **kwargs
    ) -> dict:
        payload = {
            "cmd": cmd,
            "url": url,
            "maxTimeout": max_timeout,
        }
        if "session" in kwargs:
            payload["session"] = kwargs["session"]
        if "post_data" in kwargs:
            payload["postData"] = kwargs["post_data"]
        return payload

    def request_get(
        self, url: str, max_timeout: int = 60000, session: str | None = None
    ) -> dict:
        client = self._get_client()
        payload = self._build_payload("request.get", url, max_timeout, session=session)
        resp = client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["solution"]

    def request_post(
        self,
        url: str,
        post_data: str,
        max_timeout: int = 60000,
        session: str | None = None,
    ) -> dict:
        client = self._get_client()
        payload = self._build_payload(
            "request.post", url, max_timeout, session=session, post_data=post_data
        )
        resp = client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["solution"]

    def create_session(self) -> str:
        client = self._get_client()
        payload = {"cmd": "sessions.create"}
        resp = client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["session"]

    def list_sessions(self) -> list:
        client = self._get_client()
        payload = {"cmd": "sessions.list"}
        resp = client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data.get("sessions", [])

    def destroy_session(self, session: str) -> None:
        client = self._get_client()
        payload = {"cmd": "sessions.destroy", "session": session}
        resp = client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None


class AsyncFlareSolverrClient:
    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _build_payload(
        self, cmd: str, url: str, max_timeout: int = 60000, **kwargs
    ) -> dict:
        payload = {
            "cmd": cmd,
            "url": url,
            "maxTimeout": max_timeout,
        }
        if "session" in kwargs:
            payload["session"] = kwargs["session"]
        if "post_data" in kwargs:
            payload["postData"] = kwargs["post_data"]
        return payload

    async def request_get(
        self, url: str, max_timeout: int = 60000, session: str | None = None
    ) -> dict:
        client = self._get_client()
        payload = self._build_payload("request.get", url, max_timeout, session=session)
        resp = await client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["solution"]

    async def request_post(
        self,
        url: str,
        post_data: str,
        max_timeout: int = 60000,
        session: str | None = None,
    ) -> dict:
        client = self._get_client()
        payload = self._build_payload(
            "request.post", url, max_timeout, session=session, post_data=post_data
        )
        resp = await client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["solution"]

    async def create_session(self) -> str:
        client = self._get_client()
        payload = {"cmd": "sessions.create"}
        resp = await client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data["session"]

    async def list_sessions(self) -> list:
        client = self._get_client()
        payload = {"cmd": "sessions.list"}
        resp = await client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )
        return data.get("sessions", [])

    async def destroy_session(self, session: str) -> None:
        client = self._get_client()
        payload = {"cmd": "sessions.destroy", "session": session}
        resp = await client.post(f"{self.base_url}/v1", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise FlareSolverrError(
                f"FlareSolverr error: {data.get('message', 'unknown error')}"
            )

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

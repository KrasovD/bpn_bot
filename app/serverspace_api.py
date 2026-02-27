import httpx

class ServerspaceAPI:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict:
        # По документации ключ передаётся в X-API-KEY
        return {"X-API-KEY": self.api_key, "Accept": "application/json"}

    async def get_project(self) -> dict:
        # GET /api/v1/project
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.base_url}/api/v1/project", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def list_servers(self) -> dict:
        # GET /api/v1/servers
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.base_url}/api/v1/servers", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def get_server(self, server_id: str) -> dict:
        # GET /api/v1/servers/{server_id}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.base_url}/api/v1/servers/{server_id}", headers=self._headers())
            r.raise_for_status()
            return r.json()
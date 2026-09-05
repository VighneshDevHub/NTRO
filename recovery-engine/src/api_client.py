"""
API client with authentication. Since Phase 5, POST /api/v1/operations
requires a logged-in operator — this client logs in once (or registers
first if the account doesn't exist yet) and attaches the resulting JWT
to every submission.

NOTE ON DUPLICATION: this exact file also exists in file-folder-eraser/
and recovery-engine/. Extracting it into a shared package (e.g.
forensicguard-shared on PyPI, or a local shared-lib/) is a known,
flagged cleanup item — not done yet since 3 small independent copies
was faster to ship correctly across Phases 2-4 than introducing a
shared-package dependency mid-build. Do this extraction before adding a
4th module.
"""
import httpx


class AuthenticationError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, email: str, password: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout = timeout
        self._token: str | None = None

    def _register_if_needed(self) -> None:
        httpx.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"email": self.email, "password": self.password},
            timeout=self.timeout,
        )  # 409 (already exists) is fine and expected on repeat runs — ignored either way

    def _login(self) -> str:
        resp = httpx.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            timeout=self.timeout,
        )
        if resp.status_code == 401:
            raise AuthenticationError(
                f"Login failed for {self.email}. If this is a first-time "
                f"operator, they should already have been auto-registered — "
                f"check the password matches, or the backend may be using a "
                f"different database than expected."
            )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _ensure_token(self) -> str:
        if self._token is None:
            self._register_if_needed()
            self._token = self._login()
        return self._token

    def submit_operation_report(self, report: dict) -> dict:
        token = self._ensure_token()
        response = httpx.post(
            f"{self.base_url}/api/v1/operations",
            json=report,
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        if response.status_code == 401:
            # Token may have expired mid-run — retry once with a fresh login.
            self._token = None
            token = self._ensure_token()
            response = httpx.post(
                f"{self.base_url}/api/v1/operations",
                json=report,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response.json()

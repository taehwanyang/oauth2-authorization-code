import base64
import hashlib
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import requests


AUTH_SERVER = "http://localhost:9000"
CLIENT_ID = "public-client"
REDIRECT_URI = "http://127.0.0.1:8081/callback"
SCOPE = "read"

AUTHORIZE_ENDPOINT = f"{AUTH_SERVER}/oauth2/authorize"
TOKEN_ENDPOINT = f"{AUTH_SERVER}/oauth2/token"


class OAuthCallbackState:
    def __init__(self) -> None:
        self.code: Optional[str] = None
        self.error: Optional[str] = None
        self.state: Optional[str] = None


callback_state = OAuthCallbackState()


def generate_code_verifier(length: int = 64) -> str:
    raw = base64.urlsafe_b64encode(os.urandom(length)).decode("ascii")
    verifier = raw.rstrip("=")
    if len(verifier) < 43:
        raise ValueError("Generated code_verifier is too short")
    return verifier[:128]


def generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def generate_state() -> str:
    return base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        query = urllib.parse.parse_qs(parsed.query)
        callback_state.code = query.get("code", [None])[0]
        callback_state.error = query.get("error", [None])[0]
        callback_state.state = query.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if callback_state.error:
            body = f"""
            <html>
              <body>
                <h1>OAuth Error</h1>
                <p>{callback_state.error}</p>
                <p>You can close this window.</p>
              </body>
            </html>
            """
        else:
            body = """
            <html>
              <body>
                <h1>Authorization complete</h1>
                <p>Authorization code received successfully.</p>
                <p>You can close this window.</p>
              </body>
            </html>
            """

        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        return


def run_callback_server(host: str = "127.0.0.1", port: int = 8081) -> None:
    server = HTTPServer((host, port), CallbackHandler)
    server.timeout = 300

    started_at = time.time()
    while callback_state.code is None and callback_state.error is None:
        server.handle_request()
        if time.time() - started_at > 300:
            break

    server.server_close()


def build_authorize_url(code_challenge: str, state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": SCOPE,
        "redirect_uri": REDIRECT_URI,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    response = requests.post(
        TOKEN_ENDPOINT,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        timeout=10,
    )

    print(f"[token] status={response.status_code}")
    print(f"[token] raw body={response.text}")

    response.raise_for_status()
    return response.json()


def main() -> None:
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = generate_state()

    authorize_url = build_authorize_url(code_challenge, state)

    print("=== OAuth2 Authorization Code + PKCE Client ===")
    print(f"AUTH_SERVER   : {AUTH_SERVER}")
    print(f"CLIENT_ID     : {CLIENT_ID}")
    print(f"REDIRECT_URI  : {REDIRECT_URI}")
    print(f"SCOPE         : {SCOPE}")
    print()
    print(f"code_verifier : {code_verifier}")
    print(f"code_challenge: {code_challenge}")
    print(f"state         : {state}")
    print()
    print("Opening browser...")
    print(authorize_url)
    print()

    server_thread = threading.Thread(target=run_callback_server, daemon=True)
    server_thread.start()

    opened = webbrowser.open(authorize_url)
    if not opened:
        print("Browser did not open automatically. Open this URL manually:")
        print(authorize_url)

    server_thread.join(timeout=310)

    if callback_state.error:
        raise RuntimeError(f"Authorization failed: {callback_state.error}")

    if callback_state.code is None:
        raise RuntimeError("Authorization code was not received")

    if callback_state.state != state:
        raise RuntimeError(
            f"State mismatch: expected={state}, actual={callback_state.state}"
        )

    print(f"[callback] code={callback_state.code}")
    print("[callback] state verified")
    print()

    token_response = exchange_code_for_token(callback_state.code, code_verifier)

    print()
    print("=== Token Response ===")
    print(json.dumps(token_response, indent=2, ensure_ascii=False))

    access_token = token_response.get("access_token")
    if access_token:
        print()
        print("=== Access Token ===")
        print(access_token)


if __name__ == "__main__":
    main()
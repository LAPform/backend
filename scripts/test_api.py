import os
import json
import time
import urllib.request
import urllib.parse
import http.cookiejar


BASE_URL = os.environ.get("BASE_URL", "https://backend-skum.onrender.com")


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + path


class HttpClient:
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.opener.addheaders = [("Content-Type", "application/json")]
        self.token = None

    def post_json(self, path: str, data: dict, use_bearer: bool = False):
        req = urllib.request.Request(_url(path), method="POST")
        body = json.dumps(data).encode("utf-8")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, body, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content)
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}

    def get_json(self, path: str, use_bearer: bool = False):
        req = urllib.request.Request(_url(path), method="GET")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content)
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}


def main():
    client = HttpClient()
    print(f"Testing BASE_URL={BASE_URL}")

    # 1) Health
    code, body = client.get_json("/api/health")
    print("[health]", code, body)

    # 2) Register (FST)
    ts = int(time.time())
    email = f"auto_{ts}@example.com"
    password = "Password123!"
    code, body = client.post_json(
        "/api/auth/register", {"email": email, "password": password}
    )
    print("[register]", code, body)

    # 3) Login (FST - session cookie)
    code, body = client.post_json(
        "/api/auth/login", {"email": email, "password": password}
    )
    print("[login_fst]", code, body)

    # 4) Forms list with session cookie
    code, body = client.get_json("/api/forms")
    print("[forms_list_session]", code, body)

    # 5) Login custom to get Bearer token (compat)
    code, body = client.post_json(
        "/api/auth/signin", {"email": email, "password": password}
    )
    print("[login_custom]", code, body)
    token = body.get("token") if isinstance(body, dict) else None
    client.token = token

    # 6) Create form (session or bearer). Try session first, fallback to bearer
    payload_form = {
        "title": f"Formulaire Auto {ts}",
        "description": "Test POC",
        "settings": {"theme": "blue"},
    }
    code, body = client.post_json("/api/forms", payload_form)
    if code == 401 and token:
        code, body = client.post_json("/api/forms", payload_form, use_bearer=True)
    print("[form_create]", code, body)

    form_id = None
    if isinstance(body, dict):
        form_id = (body.get("data") or {}).get("form_id")

    # 7) Add question if form created
    if form_id:
        question_payload = {
            "type": "text",
            "text": "Votre nom?",
            "required": True,
            "order_index": 0,
        }
        code, body = client.post_json(
            f"/api/forms/{form_id}/questions", question_payload
        )
        if code == 401 and token:
            code, body = client.post_json(
                f"/api/forms/{form_id}/questions", question_payload, use_bearer=True
            )
        print("[question_create]", code, body)

        # 8) Submit response
        answers = (
            {body.get("question_id", "unknown"): "John"}
            if isinstance(body, dict)
            else {}
        )
        resp_payload = {"answers": answers}
        code, body = client.post_json(f"/api/forms/{form_id}/responses", resp_payload)
        if code == 401 and token:
            code, body = client.post_json(
                f"/api/forms/{form_id}/responses", resp_payload, use_bearer=True
            )
        print("[response_submit]", code, body)

        # 9) Analytics
        code, body = client.get_json(f"/api/forms/{form_id}/analytics")
        if code == 401 and token:
            code, body = client.get_json(
                f"/api/forms/{form_id}/analytics", use_bearer=True
            )
        print("[analytics]", code, body)


if __name__ == "__main__":
    main()

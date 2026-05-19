from typing import Literal, TypedDict


class SingleIssueReviewTaskPrompt(TypedDict):
    title: str
    description: str
    code: str
    issue_line: int
    issue_severity: Literal["critical", "medium", "low"]
    issue_title: str
    issue_description: str
    issue_suggestion: str
    issue_code: str


EXTRA_PYTHON_TASK_PROMPTS: list[SingleIssueReviewTaskPrompt] = [
    {
        "title": "Load JSON config",
        "description": "Reads a JSON config file and returns the parsed object.",
        "code": """import json


def load_config(path):
    with open(path) as handle:
        return json.loads(handle)
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "String concatenation with int",
        "issue_description": "If score is numeric, the function raises TypeError while building the message.",
        "issue_suggestion": "Convert the numeric value to a string or use an f-string.",
        "issue_code": 'return f"{name}: {score}"',
    },
    {
        "title": "Group users by role",
        "description": "Collects user names under their role.",
        "code": """def group_by_role(users):
    grouped = {}
    for user in users:
        grouped[user["role"]].append(user["name"])
    return grouped
""",
        "issue_line": 4,
        "issue_severity": "medium",
        "issue_title": "Missing bucket initialization",
        "issue_description": "The first user for each role triggers a KeyError because the list is never created.",
        "issue_suggestion": "Initialize the role bucket before appending to it.",
        "issue_code": 'grouped.setdefault(user["role"], []).append(user["name"])',
    },
    {
        "title": "Build search query",
        "description": "Generates a query string for a search page.",
        "code": """def build_query(term, page):
    return f"?q={term}&page={page}"
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Values are not URL-encoded",
        "issue_description": "Spaces and special characters in the search term can break the generated query string.",
        "issue_suggestion": "Encode the parameters before building the URL.",
        "issue_code": 'from urllib.parse import urlencode\nreturn "?" + urlencode({"q": term, "page": page})',
    },
    {
        "title": "Read environment flag",
        "description": "Reads a feature flag from an environment variable.",
        "code": """import os


def feature_enabled():
    return bool(os.getenv("FEATURE_ENABLED", "false"))
""",
        "issue_line": 5,
        "issue_severity": "medium",
        "issue_title": "bool on strings is misleading",
        "issue_description": "The string 'false' is truthy, so the feature turns on when the variable is set to 'false'.",
        "issue_suggestion": "Compare the normalized string value against allowed true values.",
        "issue_code": 'return os.getenv("FEATURE_ENABLED", "false").lower() in {"1", "true", "yes"}',
    },
    {
        "title": "Choose a file extension",
        "description": "Returns the extension of a filename.",
        "code": """def get_extension(filename):
    return filename.split(".")[1]
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Missing guard for filenames without dots",
        "issue_description": "Names like 'README' raise IndexError because no extension exists.",
        "issue_suggestion": "Use rsplit with validation or pathlib for safer parsing.",
        "issue_code": 'parts = filename.rsplit(".", 1)\nif len(parts) != 2:\n    return ""\nreturn parts[1]',
    },
    {
        "title": "Find a user by id",
        "description": "Returns the first matching user record.",
        "code": """def find_user(users, user_id):
    return next(user for user in users if user["id"] == user_id)
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Lookup crashes when user is missing",
        "issue_description": "next without a default raises StopIteration when no record matches.",
        "issue_suggestion": "Provide a default or raise a clearer error.",
        "issue_code": 'return next((user for user in users if user["id"] == user_id), None)',
    },
    {
        "title": "Save identifiers to disk",
        "description": "Writes a list of ids into a file.",
        "code": """def save_ids(path, ids):
    with open(path, "w") as handle:
        handle.write(ids)
""",
        "issue_line": 3,
        "issue_severity": "medium",
        "issue_title": "write expects a string",
        "issue_description": "Passing a list directly to write raises TypeError.",
        "issue_suggestion": "Serialize the values before writing them.",
        "issue_code": 'handle.write("\n".join(ids))',
    },
    {
        "title": "Average response time",
        "description": "Returns the average latency in milliseconds.",
        "code": """def average_time(values):
    return sum(values) / len(values)
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Empty input is not handled",
        "issue_description": "An empty list still raises ZeroDivisionError.",
        "issue_suggestion": "Return a fallback or raise a clearer validation error for empty input.",
        "issue_code": "if not values:\n    return 0\nreturn sum(values) / len(values)",
    },
    {
        "title": "Keep insertion order while deduping",
        "description": "Returns a deduplicated list of names.",
        "code": """def dedupe_names(names):
    return list(set(names))
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "Order is lost",
        "issue_description": "Converting through set changes the original order of names.",
        "issue_suggestion": "Use dict.fromkeys when order should stay stable.",
        "issue_code": "return list(dict.fromkeys(names))",
    },
    {
        "title": "Normalize page number",
        "description": "Converts query input into a usable page number.",
        "code": """def parse_page(value):
    return int(value or 1)
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Negative pages are allowed",
        "issue_description": "Inputs like '-2' produce invalid pagination values instead of being rejected.",
        "issue_suggestion": "Validate that the parsed page is positive.",
        "issue_code": 'page = int(value or 1)\nif page < 1:\n    raise ValueError("page must be positive")\nreturn page',
    },
    {
        "title": "Build request headers",
        "description": "Creates request headers and adds an auth token.",
        "code": """def build_headers(token, headers={}):
    headers["Authorization"] = f"Bearer {token}"
    return headers
""",
        "issue_line": 1,
        "issue_severity": "medium",
        "issue_title": "Mutable default leaks state",
        "issue_description": "Headers from one call are reused in later calls because the same dict instance is shared.",
        "issue_suggestion": "Use None as the default and create a dict inside the function.",
        "issue_code": "def build_headers(token, headers=None):\n    headers = {} if headers is None else dict(headers)",
    },
    {
        "title": "Convert ratio to percent",
        "description": "Formats a ratio as a percent string.",
        "code": """def to_percent(value):
    return value * 100 + "%"
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Number is concatenated with string",
        "issue_description": "The code raises TypeError because it adds a number directly to a string.",
        "issue_suggestion": "Format the percent as a string.",
        "issue_code": 'return f"{value * 100}%"',
    },
    {
        "title": "Filter non-negative numbers",
        "description": "Removes negative values from a list.",
        "code": """def non_negative(values):
    return [value for value in values if value]
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Zero is filtered out too",
        "issue_description": "The truthy check drops 0 even though zero should stay in the result.",
        "issue_suggestion": "Compare against 0 explicitly.",
        "issue_code": "return [value for value in values if value >= 0]",
    },
    {
        "title": "Pick a color",
        "description": "Returns a color from a palette by index.",
        "code": """def pick_color(palette, index):
    return palette[index % len(palette)]
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Empty palette crashes",
        "issue_description": "Modulo by zero and indexing both fail when the palette is empty.",
        "issue_suggestion": "Validate palette before using it.",
        "issue_code": 'if not palette:\n    raise ValueError("palette must not be empty")\nreturn palette[index % len(palette)]',
    },
    {
        "title": "Trim markdown headings",
        "description": "Removes the leading # marker from a heading line.",
        "code": """def strip_heading(text):
    return text.lstrip("#")
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "Leading whitespace is preserved",
        "issue_description": "A heading like '# Title' becomes ' Title' with an unwanted leading space.",
        "issue_suggestion": "Strip leftover whitespace after removing the marker.",
        "issue_code": 'return text.lstrip("#").strip()',
    },
    {
        "title": "Merge tags",
        "description": "Combines two tag lists into one.",
        "code": """def merge_tags(left, right):
    return left + right
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "Duplicate tags are preserved",
        "issue_description": "The merged result can contain the same tag multiple times.",
        "issue_suggestion": "Deduplicate while preserving insertion order.",
        "issue_code": "return list(dict.fromkeys([*left, *right]))",
    },
    {
        "title": "Read the latest event",
        "description": "Returns the most recent event from a list.",
        "code": """def latest_event(events):
    return sorted(events, key=lambda event: event["created_at"])[0]
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Returns the oldest event",
        "issue_description": "Sorting ascending and taking index 0 picks the earliest event instead of the latest one.",
        "issue_suggestion": "Reverse the sort or take the last element.",
        "issue_code": 'return sorted(events, key=lambda event: event["created_at"], reverse=True)[0]',
    },
    {
        "title": "Read API timeout",
        "description": "Returns the timeout value from settings.",
        "code": """def get_timeout(settings):
    return settings.get("timeout") or 30
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "Explicit zero is overridden",
        "issue_description": "A configured timeout of 0 is treated as missing because 0 is falsy.",
        "issue_suggestion": "Only fall back when the key is absent or None.",
        "issue_code": 'timeout = settings.get("timeout")\nreturn 30 if timeout is None else timeout',
    },
    {
        "title": "Check service status",
        "description": "Maps a status code to a user-facing label.",
        "code": """STATUS_LABELS = {200: "ok", 503: "down"}


def status_label(code):
    return STATUS_LABELS[code]
""",
        "issue_line": 5,
        "issue_severity": "medium",
        "issue_title": "Unknown codes raise KeyError",
        "issue_description": "The helper crashes instead of returning a safe fallback for unexpected values.",
        "issue_suggestion": "Use get with a default label.",
        "issue_code": 'return STATUS_LABELS.get(code, "unknown")',
    },
]


FASTAPI_TASK_PROMPTS: list[SingleIssueReviewTaskPrompt] = [
    {
        "title": "Create account endpoint",
        "description": "Registers a new account from request input.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/accounts")
def create_account(payload: dict):
    return {"email": payload["email"], "role": payload.get("role", "user")}
""",
        "issue_line": 7,
        "issue_severity": "critical",
        "issue_title": "Raw dict input skips validation",
        "issue_description": "The route accepts arbitrary payload keys and shapes instead of validating the body with a request model.",
        "issue_suggestion": "Use a Pydantic model for the request body.",
        "issue_code": 'class AccountCreate(BaseModel):\n    email: EmailStr\n    role: str = "user"',
    },
    {
        "title": "Admin metrics endpoint",
        "description": "Returns a few internal admin counters.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/admin/metrics")
def admin_metrics():
    return {"users": 182, "revenue": 9200}
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Route is missing auth protection",
        "issue_description": "Sensitive metrics are exposed to any caller because the endpoint has no authorization dependency.",
        "issue_suggestion": "Require an authenticated admin dependency before returning the data.",
        "issue_code": "def admin_metrics(current_user: User = Depends(require_admin)):",
    },
    {
        "title": "Get product details",
        "description": "Looks up a product and returns it to the client.",
        "code": """from fastapi import APIRouter

router = APIRouter()
PRODUCTS = {"1": {"id": "1", "name": "Keyboard"}}


@router.get("/products/{product_id}")
def get_product(product_id: str):
    return PRODUCTS.get(product_id)
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Missing products return 200 with null",
        "issue_description": "Clients receive a successful response instead of a 404 when the product does not exist.",
        "issue_suggestion": "Raise HTTPException(status_code=404) when the record is missing.",
        "issue_code": 'product = PRODUCTS.get(product_id)\nif product is None:\n    raise HTTPException(status_code=404, detail="Product not found")',
    },
    {
        "title": "Generate report asynchronously",
        "description": "Builds a short report in an async route.",
        "code": """import time

from fastapi import APIRouter

router = APIRouter()


@router.get("/reports/daily")
async def daily_report():
    time.sleep(2)
    return {"ok": True}
""",
        "issue_line": 9,
        "issue_severity": "medium",
        "issue_title": "Blocking sleep inside async route",
        "issue_description": "time.sleep blocks the event loop and stalls other requests.",
        "issue_suggestion": "Use asyncio.sleep in async handlers.",
        "issue_code": "await asyncio.sleep(2)",
    },
    {
        "title": "Upload avatar",
        "description": "Stores an uploaded avatar on disk.",
        "code": """from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/avatars")
async def upload_avatar(file: UploadFile):
    content = await file.read()
    with open(f"/tmp/{file.filename}", "wb") as handle:
        handle.write(content)
    return {"ok": True}
""",
        "issue_line": 8,
        "issue_severity": "critical",
        "issue_title": "Filename is used directly on disk",
        "issue_description": "A crafted filename can escape the intended directory or overwrite unexpected files.",
        "issue_suggestion": "Sanitize the filename before building the path.",
        "issue_code": 'safe_name = Path(file.filename or "avatar.bin").name',
    },
    {
        "title": "Read current user",
        "description": "Returns data for the signed-in user.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def me(user_id: str):
    return {"id": user_id}
""",
        "issue_line": 7,
        "issue_severity": "critical",
        "issue_title": "User identity comes from a plain query param",
        "issue_description": "Any caller can impersonate another user by changing the user_id query value.",
        "issue_suggestion": "Resolve the current user from an auth dependency instead of trusting query input.",
        "issue_code": "async def me(current_user: User = Depends(get_current_user)):",
    },
    {
        "title": "Verify webhook",
        "description": "Receives webhook events from an external service.",
        "code": """from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/webhooks/payments")
async def payment_webhook(request: Request):
    payload = await request.json()
    return {"received": payload.get("event")}
""",
        "issue_line": 8,
        "issue_severity": "critical",
        "issue_title": "Webhook signature is not verified",
        "issue_description": "Anyone can post arbitrary events because the route never checks the provider signature header.",
        "issue_suggestion": "Verify the webhook signature before trusting the payload.",
        "issue_code": 'signature = request.headers.get("x-signature")\nverify_signature(signature, await request.body())',
    },
    {
        "title": "Create invoice asynchronously",
        "description": "Calls a repository layer and returns the created invoice.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/invoices")
async def create_invoice(payload: dict):
    invoice = save_invoice(payload)
    return invoice
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Async repository call is never awaited",
        "issue_description": "If save_invoice is async, this returns a coroutine object instead of the saved invoice.",
        "issue_suggestion": "Await the repository call in the async route.",
        "issue_code": "invoice = await save_invoice(payload)",
    },
    {
        "title": "Get database session",
        "description": "Reads invoice data with a database session.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db=get_db()):
    return db.fetch_invoice(invoice_id)
""",
        "issue_line": 7,
        "issue_severity": "critical",
        "issue_title": "Dependency is called at import time",
        "issue_description": "The database session is created once when the module loads instead of per request.",
        "issue_suggestion": "Use Depends so FastAPI manages the dependency lifecycle.",
        "issue_code": "def get_invoice(invoice_id: str, db = Depends(get_db)):",
    },
    {
        "title": "Limit search results",
        "description": "Returns matching products with a limit query param.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/search")
def search(limit: int = 10000):
    return {"limit": limit}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Limit is unbounded",
        "issue_description": "Clients can request very large limits and create unnecessary load.",
        "issue_suggestion": "Constrain the query parameter with validation.",
        "issue_code": "def search(limit: int = Query(50, ge=1, le=100)):",
    },
    {
        "title": "Export a named report",
        "description": "Loads a saved report by filename.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/reports/{filename}")
def export_report(filename: str):
    with open(f"/tmp/reports/{filename}") as handle:
        return {"content": handle.read()}
""",
        "issue_line": 8,
        "issue_severity": "critical",
        "issue_title": "Route parameter is used in a filesystem path",
        "issue_description": "Path traversal is possible because the filename is never sanitized.",
        "issue_suggestion": "Use Path(filename).name or reject unsafe path segments.",
        "issue_code": "safe_name = Path(filename).name",
    },
    {
        "title": "Create team membership",
        "description": "Adds a user to a team and returns the saved record.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/teams/{team_id}/members", status_code=200)
def add_member(team_id: str, payload: dict):
    return {"team_id": team_id, "user_id": payload["user_id"]}
""",
        "issue_line": 6,
        "issue_severity": "low",
        "issue_title": "Create route returns 200 instead of 201",
        "issue_description": "A resource-creation endpoint should report creation semantics with a 201 response.",
        "issue_suggestion": "Return HTTP 201 for successful creation.",
        "issue_code": '@router.post("/teams/{team_id}/members", status_code=201)',
    },
    {
        "title": "Send email in background",
        "description": "Schedules an email after a purchase is created.",
        "code": """from fastapi import APIRouter, BackgroundTasks

router = APIRouter()


@router.post("/purchases")
def create_purchase(background_tasks: BackgroundTasks, payload: dict):
    send_receipt_email(payload["email"])
    return {"ok": True}
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "BackgroundTasks is not used",
        "issue_description": "The email is sent inline, which slows the request instead of deferring the work.",
        "issue_suggestion": "Schedule the side effect through BackgroundTasks.",
        "issue_code": 'background_tasks.add_task(send_receipt_email, payload["email"])',
    },
    {
        "title": "Handle duplicate email",
        "description": "Creates a customer record in the database.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/customers")
def create_customer(payload: dict):
    customer = repo.create(payload)
    return customer
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Repository errors are not translated",
        "issue_description": "A duplicate email from the repository can bubble up as a 500 instead of a useful client error.",
        "issue_suggestion": "Catch uniqueness errors and return a 409 or 400 response.",
        "issue_code": 'except DuplicateEmailError:\n    raise HTTPException(status_code=409, detail="Email already exists")',
    },
    {
        "title": "Return a public user response",
        "description": "Reads a user and returns it to the client.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/users/{user_id}")
def get_user(user_id: str):
    return repo.get_user(user_id)
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Response shape is unconstrained",
        "issue_description": "Returning the raw repository object can expose internal fields that should not leave the API.",
        "issue_suggestion": "Declare a response_model for the public schema.",
        "issue_code": '@router.get("/users/{user_id}", response_model=UserRead)',
    },
    {
        "title": "Reuse an HTTP client",
        "description": "Calls an internal API from a route handler.",
        "code": """import httpx
from fastapi import APIRouter

router = APIRouter()


@router.get("/sync")
async def sync_data():
    client = httpx.AsyncClient()
    response = await client.get("https://example.com/data")
    return response.json()
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Async client is never closed",
        "issue_description": "The route creates a new client every call and leaks the connection pool lifecycle.",
        "issue_suggestion": "Use 'async with' or a shared managed client.",
        "issue_code": 'async with httpx.AsyncClient() as client:\n    response = await client.get("https://example.com/data")',
    },
    {
        "title": "Filter archived projects",
        "description": "Returns a project list with an optional archived flag.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.get("/projects")
def list_projects(include_archived: str = "false"):
    return {"include_archived": bool(include_archived)}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "String-to-bool conversion is wrong",
        "issue_description": "bool('false') evaluates to True, so archived projects are always included when the param is present.",
        "issue_suggestion": "Type the query param as bool so FastAPI parses it correctly.",
        "issue_code": "def list_projects(include_archived: bool = False):",
    },
    {
        "title": "Read raw JSON body",
        "description": "Processes a free-form event payload.",
        "code": """from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/events")
async def create_event(request: Request):
    payload = await request.json()
    return {"event": payload["event"]}
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Malformed JSON becomes a 500",
        "issue_description": "Invalid request bodies raise parsing errors that are not translated into a useful client response.",
        "issue_suggestion": "Validate the body with a schema or catch decode errors explicitly.",
        "issue_code": "class EventCreate(BaseModel):\n    event: str",
    },
    {
        "title": "Bulk update task status",
        "description": "Updates many task ids to a new status.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/tasks/bulk-status")
def bulk_status(payload: dict):
    for task_id in payload.get("ids", []):
        repo.set_status(task_id, payload["status"])
    return {"ok": True}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Empty id lists are silently accepted",
        "issue_description": "The endpoint reports success even when no ids are provided, which hides client mistakes.",
        "issue_suggestion": "Validate that at least one id is present.",
        "issue_code": 'if not payload.get("ids"):\n    raise HTTPException(status_code=400, detail="ids are required")',
    },
    {
        "title": "Refresh access token",
        "description": "Exchanges a refresh token for a new access token.",
        "code": """from fastapi import APIRouter

router = APIRouter()


@router.post("/auth/refresh")
def refresh_token(payload: dict):
    token = repo.refresh(payload["refresh_token"])
    return {"access_token": token}
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Expired token errors are not mapped",
        "issue_description": "An expired refresh token can bubble up as a generic server error instead of a clear auth failure.",
        "issue_suggestion": "Translate token errors into a 401 response.",
        "issue_code": 'except TokenExpiredError:\n    raise HTTPException(status_code=401, detail="Refresh token expired")',
    },
]


DJANGO_TASK_PROMPTS: list[SingleIssueReviewTaskPrompt] = [
    {
        "title": "Create article view",
        "description": "Creates an article from POST data.",
        "code": """from django.http import JsonResponse

from .models import Article


def create_article(request):
    article = Article.objects.create(
        title=request.POST["title"],
        body=request.POST["body"],
    )
    return JsonResponse({"id": article.id})
""",
        "issue_line": 7,
        "issue_severity": "critical",
        "issue_title": "POST data is used without form validation",
        "issue_description": "The view trusts raw request.POST values instead of validating required fields and types.",
        "issue_suggestion": "Validate input with a Django form or serializer before saving.",
        "issue_code": 'form = ArticleForm(request.POST)\nif not form.is_valid():\n    return JsonResponse({"errors": form.errors}, status=400)',
    },
    {
        "title": "Edit profile view",
        "description": "Updates a user's own profile fields.",
        "code": """from django.shortcuts import get_object_or_404, redirect

from .models import Profile


def edit_profile(request, profile_id):
    profile = get_object_or_404(Profile, pk=profile_id)
    profile.bio = request.POST.get("bio", "")
    profile.save()
    return redirect("profile-detail", profile_id=profile.id)
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Ownership is never checked",
        "issue_description": "Any authenticated user can update any profile by guessing its id.",
        "issue_suggestion": "Ensure the profile belongs to the current user before saving.",
        "issue_code": "if profile.user_id != request.user.id:\n    return HttpResponseForbidden()",
    },
    {
        "title": "Generate product slug",
        "description": "Creates a slug from the product name before save.",
        "code": """from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
""",
        "issue_line": 9,
        "issue_severity": "medium",
        "issue_title": "Slug changes on every update",
        "issue_description": "Editing the product name later changes the slug and can break existing URLs.",
        "issue_suggestion": "Only set the slug when it is empty.",
        "issue_code": "if not self.slug:\n    self.slug = slugify(self.name)",
    },
    {
        "title": "Delete comment route",
        "description": "Removes a comment and redirects back.",
        "code": """from django.shortcuts import get_object_or_404, redirect

from .models import Comment


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.delete()
    return redirect("comments-list")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Destructive action accepts GET requests",
        "issue_description": "The view deletes data regardless of HTTP method, which is unsafe and CSRF-prone.",
        "issue_suggestion": "Require POST and add CSRF protection for deletion.",
        "issue_code": 'if request.method != "POST":\n    return HttpResponseNotAllowed(["POST"])',
    },
    {
        "title": "Project dashboard",
        "description": "Shows a dashboard of recent projects.",
        "code": """from django.shortcuts import render

from .models import Project


def dashboard(request):
    projects = Project.objects.order_by("-created_at")[:10]
    return render(request, "dashboard.html", {"projects": projects})
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Dashboard is public",
        "issue_description": "Anyone can load internal project data because the view has no authentication requirement.",
        "issue_suggestion": "Protect the view with login_required.",
        "issue_code": "@login_required",
    },
    {
        "title": "Invoice detail page",
        "description": "Loads and renders a single invoice.",
        "code": """from django.shortcuts import render

from .models import Invoice


def invoice_detail(request, invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)
    return render(request, "invoice_detail.html", {"invoice": invoice})
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Missing object lookup handling",
        "issue_description": "A missing invoice raises DoesNotExist and becomes a 500 error.",
        "issue_suggestion": "Use get_object_or_404 for detail views.",
        "issue_code": "invoice = get_object_or_404(Invoice, pk=invoice_id)",
    },
    {
        "title": "Search customers",
        "description": "Runs a quick search over customer names.",
        "code": """from django.db import connection
from django.http import JsonResponse


def search_customers(request):
    term = request.GET.get("q", "")
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, name FROM customers WHERE name LIKE '%{term}%'")
        rows = cursor.fetchall()
    return JsonResponse({"rows": rows})
""",
        "issue_line": 8,
        "issue_severity": "critical",
        "issue_title": "Raw SQL is interpolated with user input",
        "issue_description": "The query is vulnerable to SQL injection because the search term is inserted directly into the SQL string.",
        "issue_suggestion": "Use parameterized queries or the ORM.",
        "issue_code": 'cursor.execute("SELECT id, name FROM customers WHERE name LIKE %s", [f"%{term}%"])',
    },
    {
        "title": "Upload avatar form",
        "description": "Stores an uploaded avatar file for a profile.",
        "code": """from django.core.files.storage import default_storage
from django.http import JsonResponse


def upload_avatar(request):
    file = request.FILES["avatar"]
    path = default_storage.save(file.name, file)
    return JsonResponse({"path": path})
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Original upload name is trusted",
        "issue_description": "Saving under the raw client filename can cause collisions and unpleasant names in storage.",
        "issue_suggestion": "Generate a server-side filename before saving.",
        "issue_code": 'path = default_storage.save(f"avatars/{uuid4()}-{file.name}", file)',
    },
    {
        "title": "Add cart item",
        "description": "Stores a cart quantity inside the session.",
        "code": """from django.shortcuts import redirect


def add_to_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart[product_id] = request.POST.get("qty", 1)
    request.session["cart"] = cart
    return redirect("cart-detail")
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Quantity is stored as raw text",
        "issue_description": "The session ends up with strings or invalid values instead of validated integers.",
        "issue_suggestion": "Parse and validate qty before saving it.",
        "issue_code": 'qty = int(request.POST.get("qty", 1))',
    },
    {
        "title": "Publish post form",
        "description": "Marks a post as published from a management action.",
        "code": """from django.shortcuts import get_object_or_404, redirect

from .models import Post


def publish_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.status = "published"
    post.save()
    return redirect("post-detail", post_id=post.id)
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "View ignores request method",
        "issue_description": "Publishing content should not happen on GET requests.",
        "issue_suggestion": "Require POST before applying the state change.",
        "issue_code": 'if request.method != "POST":\n    return HttpResponseNotAllowed(["POST"])',
    },
    {
        "title": "Task list for a board",
        "description": "Renders tasks belonging to a board.",
        "code": """from django.shortcuts import render

from .models import Task


def board_tasks(request, board_id):
    tasks = Task.objects.filter(board_id=board_id)
    return render(request, "board_tasks.html", {"tasks": tasks})
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Board ownership is not enforced",
        "issue_description": "Users can inspect tasks from any board id if there is no membership check.",
        "issue_suggestion": "Verify that the current user can access the board before querying tasks.",
        "issue_code": "board = get_object_or_404(Board, pk=board_id, members=request.user)",
    },
    {
        "title": "Update site settings",
        "description": "Applies site settings changes from an admin screen.",
        "code": """from django.shortcuts import redirect

from .models import SiteSettings


def update_settings(request):
    settings = SiteSettings.objects.first()
    settings.support_email = request.POST.get("support_email", "")
    settings.save()
    return redirect("settings")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Admin-only action is unprotected",
        "issue_description": "Any signed-in user can update global site settings if the route is exposed.",
        "issue_suggestion": "Require a staff-only check before writing settings.",
        "issue_code": "if not request.user.is_staff:\n    return HttpResponseForbidden()",
    },
    {
        "title": "Register user",
        "description": "Creates a new user account from form data.",
        "code": """from django.contrib.auth.models import User
from django.shortcuts import redirect


def register(request):
    user = User.objects.create(
        username=request.POST["username"],
        password=request.POST["password"],
    )
    return redirect("login")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Password is stored in plain text",
        "issue_description": "User.objects.create bypasses password hashing and stores the raw password value.",
        "issue_suggestion": "Use create_user so Django hashes the password correctly.",
        "issue_code": 'user = User.objects.create_user(username=request.POST["username"], password=request.POST["password"])',
    },
    {
        "title": "Render order list",
        "description": "Shows recent orders and each related customer.",
        "code": """from django.shortcuts import render

from .models import Order


def order_list(request):
    orders = Order.objects.order_by("-created_at")[:50]
    return render(request, "order_list.html", {"orders": orders})
""",
        "issue_line": 6,
        "issue_severity": "low",
        "issue_title": "Related customer data can trigger N+1 queries",
        "issue_description": "Rendering customer info per order in the template can issue many extra queries.",
        "issue_suggestion": "Use select_related for the customer relation.",
        "issue_code": 'orders = Order.objects.select_related("customer").order_by("-created_at")[:50]',
    },
    {
        "title": "Newsletter subscribers export",
        "description": "Returns a CSV of newsletter subscribers.",
        "code": """from django.http import HttpResponse

from .models import Subscriber


def export_subscribers(request):
    emails = "\n".join(Subscriber.objects.values_list("email", flat=True))
    return HttpResponse(emails, content_type="text/csv")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Export endpoint is not protected",
        "issue_description": "Sensitive email addresses are downloadable without an access check.",
        "issue_suggestion": "Require staff or admin authorization for exports.",
        "issue_code": "@staff_member_required",
    },
    {
        "title": "Invite team member",
        "description": "Creates a new invitation record for a team.",
        "code": """from django.shortcuts import redirect

from .models import Invite


def invite_member(request, team_id):
    Invite.objects.create(team_id=team_id, email=request.POST["email"])
    return redirect("team-detail", team_id=team_id)
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Email is not normalized",
        "issue_description": "Different letter casing can create duplicate invites for the same address.",
        "issue_suggestion": "Normalize the email before saving it.",
        "issue_code": 'email = request.POST["email"].strip().lower()',
    },
    {
        "title": "Comment moderation queue",
        "description": "Shows comments awaiting moderation.",
        "code": """from django.shortcuts import render

from .models import Comment


def moderation_queue(request):
    comments = Comment.objects.filter(status="pending")
    return render(request, "moderation_queue.html", {"comments": comments})
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Moderation screen is not staff-only",
        "issue_description": "Pending moderation data is exposed without checking staff permissions.",
        "issue_suggestion": "Restrict the view to staff users.",
        "issue_code": "@staff_member_required",
    },
    {
        "title": "Mark notification read",
        "description": "Sets a notification as read for the current user.",
        "code": """from django.shortcuts import get_object_or_404, redirect

from .models import Notification


def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    notification.read = True
    notification.save()
    return redirect("notifications")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Notification ownership is ignored",
        "issue_description": "A user can mark another user's notification as read by guessing its id.",
        "issue_suggestion": "Load the notification through the current user relationship.",
        "issue_code": "notification = get_object_or_404(Notification, pk=notification_id, user=request.user)",
    },
    {
        "title": "Search blog posts",
        "description": "Returns blog posts matching a search term.",
        "code": """from django.shortcuts import render

from .models import Post


def search_posts(request):
    posts = Post.objects.filter(title__icontains=request.GET["q"])
    return render(request, "search.html", {"posts": posts})
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Missing query param handling",
        "issue_description": "Accessing request.GET['q'] raises KeyError when the user loads the page without a search term.",
        "issue_suggestion": "Use get with a safe default.",
        "issue_code": 'query = request.GET.get("q", "")',
    },
    {
        "title": "Approve reimbursement",
        "description": "Marks a reimbursement request as approved.",
        "code": """from django.shortcuts import get_object_or_404, redirect

from .models import Reimbursement


def approve_reimbursement(request, reimbursement_id):
    reimbursement = get_object_or_404(Reimbursement, pk=reimbursement_id)
    reimbursement.status = "approved"
    reimbursement.save()
    return redirect("reimbursements")
""",
        "issue_line": 6,
        "issue_severity": "critical",
        "issue_title": "Approval action is not permission-gated",
        "issue_description": "Anyone who can hit the route can approve reimbursements.",
        "issue_suggestion": "Require the proper manager permission before updating the status.",
        "issue_code": 'if not request.user.has_perm("billing.can_approve_reimbursement"):\n    return HttpResponseForbidden()',
    },
]


REACT_TASK_PROMPTS: list[SingleIssueReviewTaskPrompt] = [
    {
        "title": "Add todo item",
        "description": "Adds a new todo into local component state.",
        "code": """import { useState } from "react";

export default function TodoList() {
  const [items, setItems] = useState([]);

  function addItem(label) {
    items.push({ id: Date.now(), label });
    setItems(items);
  }

  return <button onClick={() => addItem("New")}>Add</button>;
}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "State array is mutated in place",
        "issue_description": "React may miss the change because the same array reference is reused.",
        "issue_suggestion": "Create a new array when updating state.",
        "issue_code": "setItems((current) => [...current, { id: Date.now(), label }]);",
    },
    {
        "title": "Load a user profile",
        "description": "Fetches profile data whenever the selected user changes.",
        "code": """import { useEffect, useState } from "react";

export default function Profile({ userId }) {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((response) => response.json())
      .then(setProfile);
  }, []);

    return <pre>{JSON.stringify(profile)}</pre>;
}
""",
        "issue_line": 10,
        "issue_severity": "medium",
        "issue_title": "Effect ignores userId changes",
        "issue_description": "The request only runs once, so switching to a different user leaves stale profile data on screen.",
        "issue_suggestion": "Include userId in the effect dependency list.",
        "issue_code": "}, [userId]);",
    },
    {
        "title": "Live clock component",
        "description": "Updates the time every second.",
        "code": """import { useEffect, useState } from "react";

export default function Clock() {
    const [value, setValue] = useState(Date.now());

    useEffect(() => {
        setInterval(() => {
            setValue(Date.now());
        }, 1000);
    }, []);

    return <span>{value}</span>;
}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Interval is never cleaned up",
        "issue_description": "The timer keeps running after the component unmounts and leaks work.",
        "issue_suggestion": "Store the timer id and clear it in the cleanup function.",
        "issue_code": "const timerId = setInterval(() => {\n  setValue(Date.now());\n}, 1000);\nreturn () => clearInterval(timerId);",
    },
    {
        "title": "Render message list",
        "description": "Shows a list of messages in order.",
        "code": """export default function MessageList({ messages }) {
    return (
        <ul>
            {messages.map((message, index) => (
                <li key={index}>{message.text}</li>
            ))}
        </ul>
    );
}
""",
        "issue_line": 4,
        "issue_severity": "low",
        "issue_title": "Array index is used as the key",
        "issue_description": "Reordering or inserting messages can confuse React reconciliation and produce stale rows.",
        "issue_suggestion": "Use a stable message id as the key.",
        "issue_code": "key={message.id}",
    },
    {
        "title": "Increment twice",
        "description": "Advances a counter by two when the button is clicked.",
        "code": """import { useState } from "react";

export default function Counter() {
    const [count, setCount] = useState(0);

  function handleClick() {
    setCount(count + 1);
    setCount(count + 1);
  }

  return <button onClick={handleClick}>{count}</button>;
}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Updates use stale state",
        "issue_description": "Both updates capture the same count value, so the counter only increments once.",
        "issue_suggestion": "Use the functional state updater when the next state depends on the previous value.",
        "issue_code": "setCount((current) => current + 1);\nsetCount((current) => current + 1);",
    },
    {
        "title": "Mirror prop into state",
        "description": "Keeps an editable draft name in local state.",
        "code": """import { useState } from "react";

export default function NameEditor({ name }) {
  const [draft, setDraft] = useState(name);

  return <input value={draft} onChange={(event) => setDraft(event.target.value)} />;
}
""",
        "issue_line": 4,
        "issue_severity": "medium",
        "issue_title": "Local state does not react to prop changes",
        "issue_description": "If the parent passes a new name, the draft stays stuck on the first render value.",
        "issue_suggestion": "Sync the local draft when the prop changes or avoid duplicating the prop in state.",
        "issue_code": "useEffect(() => {\n  setDraft(name);\n}, [name]);",
    },
    {
        "title": "Search box request",
        "description": "Fetches suggestions for the current search term.",
        "code": """import { useEffect, useState } from "react";

export default function SearchBox({ term }) {
  const [results, setResults] = useState([]);

  useEffect(() => {
    fetch(`/api/search?q=${term}`)
      .then((response) => response.json())
      .then(setResults);
  }, [term]);

  return <div>{results.length}</div>;
}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Stale requests can win the race",
        "issue_description": "A slower response for an older term can overwrite the latest results.",
        "issue_suggestion": "Cancel stale requests or ignore outdated responses.",
        "issue_code": "const controller = new AbortController();\nfetch(`/api/search?q=${term}`, { signal: controller.signal })\nreturn () => controller.abort();",
    },
    {
        "title": "Toggle panel visibility",
        "description": "Shows and hides a details panel.",
        "code": """import { useState } from "react";

export default function PanelToggle() {
  const [open, setOpen] = useState(false);

  return <button onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"}</button>;
}
""",
        "issue_line": 6,
        "issue_severity": "low",
        "issue_title": "Toggle uses captured state",
        "issue_description": "A functional updater is safer when multiple events can queue before render.",
        "issue_suggestion": "Toggle from the current state value passed by React.",
        "issue_code": "onClick={() => setOpen((current) => !current)}",
    },
    {
        "title": "Profile avatar image",
        "description": "Displays a profile avatar from a remote URL.",
        "code": """export default function Avatar({ user }) {
  return <img src={user.avatarUrl} />;
}
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "Image lacks accessible alt text",
        "issue_description": "Screen readers do not get a useful description of the avatar.",
        "issue_suggestion": "Provide an informative alt attribute.",
        "issue_code": "return <img src={user.avatarUrl} alt={`${user.name} avatar`} />;",
    },
    {
        "title": "Sort products in render",
        "description": "Shows a sorted list of products.",
        "code": """export default function ProductList({ products }) {
  products.sort((left, right) => left.name.localeCompare(right.name));

  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Props are mutated during render",
        "issue_description": "Sorting the incoming array changes parent-owned data and can cause surprising side effects.",
        "issue_suggestion": "Sort a copy instead of mutating props.",
        "issue_code": "const sortedProducts = [...products].sort((left, right) => left.name.localeCompare(right.name));",
    },
    {
        "title": "Filter list items",
        "description": "Builds a filtered list from a query string.",
        "code": """import { useState } from "react";

export default function FilteredList({ items }) {
  const [query, setQuery] = useState("");
  const visible = items.filter((item) => item.name.includes(query.toLowerCase()));

  return <input value={query} onChange={(event) => setQuery(event.target.value)} />;
}
""",
        "issue_line": 5,
        "issue_severity": "medium",
        "issue_title": "Comparison normalizes only one side",
        "issue_description": "Lowercasing the query but not the item name makes filtering case-sensitive in one direction.",
        "issue_suggestion": "Normalize both values before comparing.",
        "issue_code": "const visible = items.filter((item) => item.name.toLowerCase().includes(query.toLowerCase()));",
    },
    {
        "title": "Map notification count",
        "description": "Displays the unread notification count.",
        "code": """export default function NotificationBadge({ notifications }) {
  const unread = notifications.filter((notification) => !notification.read).length;

  if (!unread) {
    return 0;
  }

  return <span>{unread}</span>;
}
""",
        "issue_line": 5,
        "issue_severity": "low",
        "issue_title": "Component returns a bare number",
        "issue_description": "Returning 0 renders text unexpectedly instead of rendering nothing.",
        "issue_suggestion": "Return null when the badge should be hidden.",
        "issue_code": "if (!unread) {\n  return null;\n}",
    },
    {
        "title": "Compose CSS classes",
        "description": "Builds a class string for a button.",
        "code": """export default function Button({ primary }) {
  const className = ["button", primary && "button-primary"].join(" ");
  return <button className={className}>Save</button>;
}
""",
        "issue_line": 2,
        "issue_severity": "low",
        "issue_title": "False values leak into the class list",
        "issue_description": "When primary is false, the class string becomes 'button false'.",
        "issue_suggestion": "Filter falsy entries before joining.",
        "issue_code": 'const className = ["button", primary && "button-primary"].filter(Boolean).join(" ");',
    },
    {
        "title": "Render a Markdown preview",
        "description": "Shows Markdown coming from user input.",
        "code": """export default function Preview({ html }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
""",
        "issue_line": 2,
        "issue_severity": "critical",
        "issue_title": "Unsanitized HTML is rendered directly",
        "issue_description": "User-controlled HTML can execute scripts in the browser.",
        "issue_suggestion": "Sanitize HTML before rendering or render Markdown safely.",
        "issue_code": "const safeHtml = DOMPurify.sanitize(html);",
    },
    {
        "title": "Handle form submission",
        "description": "Saves a profile form when the user submits it.",
        "code": """export default function ProfileForm() {
  function handleSubmit() {
    fetch("/api/profile", { method: "POST" });
  }

  return <form onSubmit={handleSubmit}><button type="submit">Save</button></form>;
}
""",
        "issue_line": 2,
        "issue_severity": "medium",
        "issue_title": "Submit handler does not prevent default",
        "issue_description": "The browser performs a full page reload before the fetch can complete.",
        "issue_suggestion": "Accept the submit event and call preventDefault().",
        "issue_code": "function handleSubmit(event) {\n  event.preventDefault();",
    },
    {
        "title": "Read window width",
        "description": "Shows the current viewport width.",
        "code": """import { useEffect, useState } from "react";

export default function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    window.addEventListener("resize", () => setWidth(window.innerWidth));
  }, []);

  return <span>{width}</span>;
}
""",
        "issue_line": 7,
        "issue_severity": "medium",
        "issue_title": "Resize listener is never removed",
        "issue_description": "The component leaks event listeners across mounts.",
        "issue_suggestion": "Store the handler and remove it in cleanup.",
        "issue_code": 'const handleResize = () => setWidth(window.innerWidth);\nwindow.addEventListener("resize", handleResize);\nreturn () => window.removeEventListener("resize", handleResize);',
    },
    {
        "title": "Update selected tab",
        "description": "Shows the content of the currently active tab.",
        "code": """import { useState } from "react";

export default function Tabs({ items }) {
  const [selectedId, setSelectedId] = useState(items[0].id);

  return (
    <div>
      {items.map((item) => (
        <button key={item.id} onClick={setSelectedId(item.id)}>{item.label}</button>
      ))}
    </div>
  );
}
""",
        "issue_line": 8,
        "issue_severity": "medium",
        "issue_title": "Click handler executes during render",
        "issue_description": "setSelectedId runs immediately instead of when the button is clicked.",
        "issue_suggestion": "Wrap the state update in a function.",
        "issue_code": "onClick={() => setSelectedId(item.id)}",
    },
    {
        "title": "Fetch project list once",
        "description": "Loads projects and stores them in component state.",
        "code": """import { useEffect, useState } from "react";

export default function Projects() {
  const [projects, setProjects] = useState([]);

  useEffect(async () => {
    const response = await fetch("/api/projects");
    const data = await response.json();
    setProjects(data);
  }, []);

  return <div>{projects.length}</div>;
}
""",
        "issue_line": 6,
        "issue_severity": "medium",
        "issue_title": "Effect callback is async",
        "issue_description": "useEffect expects a cleanup function or nothing, not a Promise.",
        "issue_suggestion": "Create an inner async function and call it from the effect.",
        "issue_code": "useEffect(() => {\n  async function loadProjects() {\n    ...\n  }\n  loadProjects();\n}, []);",
    },
    {
        "title": "Toggle favorite product",
        "description": "Adds or removes a product id from favorites.",
        "code": """import { useState } from "react";

export default function FavoriteToggle({ productId }) {
  const [favorites, setFavorites] = useState([]);

  function toggleFavorite() {
    if (favorites.includes(productId)) {
      setFavorites(favorites.filter((id) => id !== productId));
      return;
    }

    setFavorites([...favorites, productId]);
  }

  return <button onClick={toggleFavorite}>Toggle</button>;
}
""",
        "issue_line": 6,
        "issue_severity": "low",
        "issue_title": "Updates depend on captured state",
        "issue_description": "Queued clicks can apply stale favorite state.",
        "issue_suggestion": "Use a functional state update based on the latest array.",
        "issue_code": "setFavorites((current) => current.includes(productId) ? current.filter((id) => id !== productId) : [...current, productId]);",
    },
    {
        "title": "Render theme from localStorage",
        "description": "Reads a persisted theme from localStorage.",
        "code": """import { useState } from "react";

export default function ThemeLabel() {
  const [theme] = useState(localStorage.getItem("theme") || "light");
  return <span>{theme}</span>;
}
""",
        "issue_line": 4,
        "issue_severity": "medium",
        "issue_title": "Browser API is read during render",
        "issue_description": "Direct localStorage access breaks in server rendering and makes initialization harder to control.",
        "issue_suggestion": "Use a lazy initializer guarded for the browser.",
        "issue_code": 'const [theme] = useState(() => window.localStorage.getItem("theme") || "light");',
    },
]

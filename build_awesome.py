#!/usr/bin/env python3
"""Fetch top GitHub repos per topic via `gh api`, write a README.md per subfolder.
ponytail: stars are a live snapshot, dated in each file; re-run to refresh."""
import json, subprocess, os, sys

ROOT = "/home/avinash/Documents/awesome-github-repo"
DATE = "2026-07-15"
PER = 35

# topic -> (Title, blurb, search query, [extra explicit repos owner/name])
TOPICS = {
    "claude-code":        ("Claude Code", "Plugins, agents, skills & tooling for Claude Code.",
                           "claude code in:name,description", ["anthropics/claude-code", "hesreallyhim/awesome-claude-code"]),
    "contribution":       ("Open-Source Contribution", "Beginner-friendly repos & good-first-issue hubs.",
                           "first contributions in:name,description", ["firstcontributions/first-contributions", "MunGell/awesome-for-beginners"]),
    "python-projects":    ("Python Projects", "Top starred Python projects to learn from.",
                           "language:python", ["public-apis/public-apis", "TheAlgorithms/Python"]),
    "python-tools":       ("Python Tools", "CLI tools, linters, package & dev tooling in Python.",
                           "python tool in:name,description language:python", ["astral-sh/ruff", "astral-sh/uv", "pydantic/pydantic"]),
    "fastapi":            ("FastAPI", "FastAPI framework, extensions & starter templates.",
                           "topic:fastapi", ["fastapi/fastapi", "fastapi/full-stack-fastapi-template", "tiangolo/sqlmodel"]),
    "observability":      ("Observability & Monitoring", "SigNoz, Prometheus, Grafana, OpenTelemetry, ELK.",
                           "observability in:name,description", ["SigNoz/signoz", "prometheus/prometheus", "grafana/grafana", "open-telemetry/opentelemetry-collector", "elastic/elasticsearch"]),
    "load-balancing-cdn": ("Load Balancing & CDN", "Reverse proxies, load balancers, edge & CDN.",
                           "reverse proxy load balancer in:name,description", ["traefik/traefik", "caddyserver/caddy", "nginx/nginx", "haproxy/haproxy"]),
    "celery-redis":       ("Job Queues (Celery + Redis)", "Task queues, background jobs & schedulers.",
                           "task queue job queue in:name,description", ["celery/celery", "rq/rq", "hatchet-dev/hatchet"]),
    "ci-cd":              ("CI/CD", "Continuous integration & delivery pipelines.",
                           "ci cd pipeline in:name,description", ["actions/runner", "argoproj/argo-cd", "gitea/gitea"]),
    "postgresql":         ("PostgreSQL", "Postgres server, extensions, tooling & clients.",
                           "postgres in:name", ["postgres/postgres", "supabase/supabase", "pgvector/pgvector", "postgrespro/postgres"]),
    "redis":              ("Redis & Caching", "Redis, caching layers & in-memory stores.",
                           "redis in:name", ["redis/redis", "valkey-io/valkey", "dragonflydb/dragonfly", "redisson/redisson"]),
    "message-brokers":    ("Message Brokers (Kafka / RabbitMQ)", "Event streaming & message queues.",
                           "kafka rabbitmq message broker in:name,description", ["apache/kafka", "rabbitmq/rabbitmq-server", "redpanda-data/redpanda", "nats-io/nats-server"]),
    "docker":             ("Docker & Containers", "Container runtimes, images & Docker tooling.",
                           "docker in:name", ["moby/moby", "docker/compose", "docker/awesome-compose", "docker/cli"]),
    "kubernetes":         ("Kubernetes", "K8s core, operators, GitOps & cluster tooling.",
                           "kubernetes in:name", ["kubernetes/kubernetes", "helm/helm", "k3s-io/k3s", "argoproj/argo-cd"]),
    # --- infra / backend ---
    "terraform-iac":      ("Terraform & IaC", "Infrastructure as code: Terraform, Pulumi, Ansible.",
                           "terraform in:name", ["hashicorp/terraform", "pulumi/pulumi", "ansible/ansible", "gruntwork-io/terragrunt", "aquasecurity/tfsec"]),
    "web-servers":        ("Web Servers (Nginx / Caddy)", "Nginx, Caddy, OpenResty & HTTP servers.",
                           "nginx in:name", ["nginx/nginx", "caddyserver/caddy", "openresty/openresty", "apache/httpd"]),
    "elk-logging":        ("Logging (ELK / Loki)", "Elasticsearch, Logstash, Kibana, Loki, Fluentd, Vector.",
                           "logging in:name", ["elastic/elasticsearch", "elastic/logstash", "elastic/kibana", "grafana/loki", "vectordotdev/vector", "fluent/fluentd"]),
    "grpc-api":           ("gRPC & APIs", "gRPC, Protobuf, gateways & API tooling.",
                           "grpc in:name", ["grpc/grpc", "protocolbuffers/protobuf", "grpc-ecosystem/grpc-gateway", "fullstorydev/grpcurl", "connectrpc/connect-go"]),
    "sqlalchemy-orm":     ("Python ORMs", "SQLAlchemy, Alembic, Tortoise & DB layers.",
                           "orm in:name language:python", ["sqlalchemy/sqlalchemy", "sqlalchemy/alembic", "tortoise/tortoise-orm", "encode/databases", "fastapi/sqlmodel"]),
    "pytest-testing":     ("Python Testing", "pytest, tox, hypothesis & test tooling.",
                           "pytest in:name", ["pytest-dev/pytest", "tox-dev/tox", "HypothesisWorks/hypothesis", "spulec/freezegun", "nedbat/coveragepy"]),
    "async-python":       ("Async Python", "asyncio, aiohttp, httpx, uvloop, trio.",
                           "asyncio in:name", ["aio-libs/aiohttp", "encode/httpx", "MagicStack/uvloop", "python-trio/trio", "aio-libs/aiokafka"]),
    "data-pipelines":     ("Data Pipelines", "Airflow, Dagster, Prefect, dbt, Beam.",
                           "data engineering in:name,description", ["apache/airflow", "dagster-io/dagster", "PrefectHQ/prefect", "dbt-labs/dbt-core", "apache/beam"]),
    # --- career / learning ---
    "dsa-leetcode":       ("DSA & LeetCode", "Algorithms, data structures & interview coding prep.",
                           "leetcode in:name", ["TheAlgorithms/Python", "trekhleb/javascript-algorithms", "kdn251/interviews", "azl397985856/leetcode"]),
    "system-design":      ("System Design", "System design primers, patterns & scalability.",
                           "system design in:name,description", ["donnemartin/system-design-primer", "ByteByteGoHq/system-design-101", "karanpratapsingh/system-design", "ashishps1/awesome-system-design-resources"]),
    "cs-fundamentals":    ("CS Fundamentals", "Free CS courses: OS, networks, DB, theory.",
                           "computer science in:name,description", ["ossu/computer-science", "jwasham/coding-interview-university", "EbookFoundation/free-programming-books", "Developer-Y/cs-video-courses"]),
    "roadmaps":           ("Developer Roadmaps", "Learning paths & skill roadmaps.",
                           "roadmap in:name", ["kamranahmedse/developer-roadmap", "ossu/computer-science", "practical-tutorials/project-based-learning"]),
}

# group_key -> (Group Title, [topic keys in order])
GROUPS = {
    "01-dsa-interview":  ("DSA & Interview Prep (LeetCode)", ["dsa-leetcode", "system-design", "cs-fundamentals", "roadmaps"]),
    "02-backend":        ("Backend (Python / FastAPI)", ["fastapi", "sqlalchemy-orm", "async-python", "celery-redis", "grpc-api", "pytest-testing"]),
    "03-databases":      ("Databases & Messaging", ["postgresql", "redis", "message-brokers", "data-pipelines"]),
    "04-infra-devops":   ("Infra & DevOps", ["docker", "kubernetes", "terraform-iac", "web-servers", "load-balancing-cdn", "ci-cd"]),
    "05-observability":  ("Observability & Logging", ["observability", "elk-logging"]),
    "06-python":         ("Python Ecosystem", ["python-projects", "python-tools"]),
    "07-open-source":    ("Open Source & Tooling", ["claude-code", "contribution"]),
}
GROUP_OF = {k: g for g, (_, keys) in GROUPS.items() for k in keys}

def gh_search(query):
    cmd = ["gh", "api", "-X", "GET", "search/repositories",
           "-f", f"q={query}", "-f", "sort=stars", "-f", "order=desc", "-f", f"per_page={PER}"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        print(f"  ! search failed: {out.stderr.strip()[:120]}", file=sys.stderr)
        return []
    return json.loads(out.stdout).get("items", [])

def gh_repo(full):
    out = subprocess.run(["gh", "api", f"repos/{full}"], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)

def star(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)

def row(r):
    desc = (r.get("description") or "").replace("|", "\\|").strip()
    if len(desc) > 110: desc = desc[:107] + "..."
    return (r["full_name"], r["html_url"], r.get("stargazers_count", 0),
            r.get("language") or "-", desc)

summary = []
for key, (title, blurb, query, extras) in TOPICS.items():
    seen, rows = set(), []
    for r in gh_search(query):
        fn = r["full_name"]
        if fn.lower() in seen: continue
        seen.add(fn.lower()); rows.append(row(r))
    for full in extras:
        if full.lower() in seen: continue
        r = gh_repo(full)
        if r: seen.add(full.lower()); rows.append(row(r))
    rows.sort(key=lambda x: x[2], reverse=True)

    folder = os.path.join(ROOT, GROUP_OF[key], key)
    os.makedirs(folder, exist_ok=True)
    lines = [f"# Awesome {title}", "", f"> {blurb}", "",
             f"*Star counts fetched live from GitHub on {DATE}. {len(rows)} repos, sorted by stars.*", "",
             "| # | Repo | ⭐ Stars | Lang | Description |",
             "|---|------|--------:|------|-------------|"]
    for i, (fn, url, s, lang, desc) in enumerate(rows, 1):
        lines.append(f"| {i} | [{fn}]({url}) | {star(s)} | {lang} | {desc} |")
    lines.append("")
    with open(os.path.join(folder, "README.md"), "w") as f:
        f.write("\n".join(lines))
    top = rows[0][0] if rows else "-"
    summary.append((key, title, len(rows), top, rows[0][2] if rows else 0))
    print(f"[{key}] {len(rows)} repos, top: {top}")

# top-level README (nav), grouped by category
by_key = {key: (title, n, top, s) for key, title, n, top, s in summary}
total = sum(x[1] for x in by_key.values())
idx = ["# Awesome GitHub Repos", "",
       f"Curated lists of **{total} repos** across **{len(TOPICS)} topics** in **{len(GROUPS)} categories**, "
       "aligned to a Python / FastAPI / infra stack and interview prep.",
       f"Star counts fetched live from GitHub on **{DATE}**. Re-run `build_awesome.py` to refresh.", ""]
# category overview
idx += ["## Categories", "", "| Category | Topics | Repos |", "|----------|-------:|------:|"]
for g, (gtitle, keys) in GROUPS.items():
    n = sum(by_key[k][1] for k in keys if k in by_key)
    idx.append(f"| [{gtitle}](#{g}) | {len([k for k in keys if k in by_key])} | {n} |")
idx.append("")
# per-category tables
for g, (gtitle, keys) in GROUPS.items():
    idx += [f"## {g}", "", f"### {gtitle}", "", "| Topic | Repos | Top repo | ⭐ |", "|-------|------:|----------|---:|"]
    for k in keys:
        if k not in by_key: continue
        title, n, top, s = by_key[k]
        idx.append(f"| [{title}]({g}/{k}/README.md) | {n} | [{top}](https://github.com/{top}) | {star(s)} |")
    idx.append("")
idx += [f"**Total: {total} repos.**", ""]
# extra hand-curated lists (not repo-scraped)
idx += ["## Extras", "",
        "- [Boot.dev — Backend Path course tracker](boot.dev/README.md)", ""]
with open(os.path.join(ROOT, "README.md"), "w") as f:
    f.write("\n".join(idx))
print(f"\nTotal repos: {sum(x[2] for x in summary)} across {len(summary)} topics. Index written.")

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
}

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

    folder = os.path.join(ROOT, key)
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

# top-level README (nav)
total = sum(x[2] for x in summary)
idx = ["# Awesome GitHub Repos", "",
       f"Curated lists of **{total} repos** across **{len(TOPICS)} topics**, aligned to a Python / FastAPI / infra stack.",
       f"Star counts fetched live from GitHub on **{DATE}**. Re-run `build_awesome.py` to refresh.", "",
       "| Topic | Repos | Top repo | ⭐ |",
       "|-------|------:|----------|---:|"]
for key, title, n, top, s in summary:
    idx.append(f"| [{title}]({key}/README.md) | {n} | [{top}](https://github.com/{top}) | {star(s)} |")
idx += ["", f"**Total: {total} repos.**", ""]
with open(os.path.join(ROOT, "README.md"), "w") as f:
    f.write("\n".join(idx))
print(f"\nTotal repos: {sum(x[2] for x in summary)} across {len(summary)} topics. Index written.")

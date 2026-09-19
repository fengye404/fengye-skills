---
name: fengye-infra
description: Operate, troubleshoot, review, or document Fengye's personal digital infrastructure and long-lived online services. Use whenever a request concerns a durable change, incident, migration, or operating decision for personally managed computers, servers, networks, domains and DNS, websites or blog hosting, Cloudflare/CDN, deployments and CI/CD, storage and backups, remote access, proxies, identity/access, AI Agent runtimes, or similar systems—even when the specific product is not listed. Keep the private infrastructure runbook synchronized after durable findings or changes.
---

# Fengye Infra

Use the private runbook repository as the durable source of truth for Fengye's personal digital infrastructure. Treat live systems as authoritative for current state and the repository as the maintained operational record.

## Scope

Interpret “personal infrastructure” by operational responsibility, not by a fixed product list. It includes anything Fengye owns or administers that must remain understandable, reproducible, recoverable, secure, reachable, or maintainable over time, such as:

- computers, servers, VMs, containers, storage, backups, and recovery paths;
- LAN, Wi-Fi, routers, DNS, VPN/Tailscale, proxies, firewalls, and remote access;
- domains, public DNS, websites, blogs, hosting, Cloudflare/CDN/WAF, certificates, and email routing;
- deployment targets, CI/CD, source-to-production paths, scheduled jobs, and external service dependencies;
- Agent runtimes and supporting services such as Raft, OpenCode, Codex, browsers, and model gateways;
- accounts, permissions, startup behavior, observability, costs, expiry dates, migrations, incidents, and operational decisions.

The examples are non-exhaustive. A new provider or service still belongs here when it becomes part of the durable personal environment. Pure content editing does not belong here, but the hosting, deployment, domain, DNS, or recovery of that content does.

## Runbook Repository

- GitHub: `https://github.com/fengye404/agent-infrastructure-runbooks` (private)
- Canonical local path on every machine: `${FENGYE_INFRA_REPO:-$HOME/workspace/agent-infrastructure-runbooks}`
- Legacy Mac cache, if the canonical path does not yet exist: `$HOME/workspace/playground/docs`

Resolve the repository in this order:

1. Use `FENGYE_INFRA_REPO` when it points to a Git checkout.
2. Use the canonical local path.
3. Use the legacy cache only to preserve or migrate uncommitted work.
4. If no checkout exists and the task needs infrastructure context, clone the private repository into the canonical path with the authenticated `gh` CLI, falling back to ordinary `git clone` when credentials are already configured.

Before reading, check `git status`. If the checkout is clean, refresh it with `git pull --ff-only`. If it is dirty, do not overwrite, reset, or silently discard existing work; inspect the local changes and preserve them.

Read only what the task needs:

- Start with `README.md` and `agent-infrastructure-overview.md` when the relevant system is unclear.
- Read `n100-server-runbook.md` for the home Ubuntu Agent host.
- Read `tencentcloud-server-runbook.md` for the Tencent Cloud host.
- Read `web-services-runbook.md` for domains, DNS, Cloudflare, public hosting, and deployment paths.
- Use `configs/` for sanitized configuration copies.

Documentation can become stale. For decisions or changes, verify live state before acting and distinguish user-reported state, configured state, currently observed state, and reboot-tested state.

## Operating Workflow

For inspection or diagnosis, make read-only checks first and report evidence. Do not restart, rewrite, delete, expose ports, change DNS, deploy, or modify external systems unless the request authorizes the change.

For an authorized change:

1. Read the relevant runbook and inspect current live state.
2. Back up fragile configuration and preserve unrelated user changes.
3. Make the smallest scoped change and verify the actual outcome.
4. Record the change in the runbook repository during the same task.

Operational invariants in the runbooks remain binding, especially avoiding duplicate Raft Computer identities, keeping proxy/controller ports loopback-only, preserving remote-access and DNS recovery paths, and never treating a successful configuration write or deployment as proof that restart, rollback, and public reachability work.

## Required Documentation Sync

When a task produces durable personal-infrastructure information, update the runbook repository before finishing. This includes:

- host, network, service, runtime, version, address, startup, proxy, remote-access, backup, or recovery changes;
- domain, DNS, registrar, hosting, CDN/WAF, TLS, deployment, CI/CD, or public-service migrations;
- newly confirmed incidents, root causes, workarounds, pitfalls, architecture decisions, or validation results;
- installed or removed infrastructure software and external dependencies;
- configuration files or commands needed to reproduce or roll back a setup.

Update the relevant runbook's verification date and record the result, important paths, validation, and rollback boundary. Add sanitized configuration copies under `configs/` when they materially aid recovery. Update the overview when roles, entry points, providers, or architecture change. If a new infrastructure category has no runbook yet, create an appropriately named runbook rather than forcing it into an unrelated machine document.

Then synchronize the private repository:

1. Review `git status` and stage only files belonging to the current work.
2. Run `git diff --cached --check` and inspect the staged diff for secrets.
3. Commit with a concise operational message.
4. Reconcile with `origin/main` without discarding work, then push to `origin/main`.
5. If authentication, conflicts, or remote availability prevent pushing, keep the local commit and clearly report what remains unsynchronized.

Documentation synchronization is expected for completed infrastructure work, but it does not grant permission for unrelated live-system changes.

## Secret Boundary

Never commit or print passwords, SSH private keys, cookies, access or refresh tokens, API keys, proxy subscription URLs, node credentials, Raft login tokens, router sessions, RDP secrets, registrar recovery codes, encrypted credential payloads, or complete sensitive profiles. Record only the mechanism, owning system, sanitized path, and recovery procedure. Public keys, non-secret IDs, public/LAN/Tailscale addresses, versions, provider names, and redacted configuration examples may be documented when useful.

## Skill Source and Cross-Machine Installation

This Skill's only source of truth is `https://github.com/fengye404/fengye-skills`, normally cloned at `~/workspace/fengye-skills`. Do not duplicate the Skill inside the runbook repository. On a new machine, clone both private repositories and run `~/workspace/fengye-skills/install.sh`; the installer creates the tool-specific symlinks, while this Skill locates operational records in the runbook repository.

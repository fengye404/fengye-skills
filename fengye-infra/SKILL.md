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

## Upgrading the System Running the Agent

When an Agent upgrades its own host platform (for example, a Raft Agent upgrading Raft Server or Computer), treat loss of the executing Agent as an expected failure mode. An upgrade request includes necessary recovery preparation and post-upgrade verification; do not rely on a follow-up chat through the system being replaced.

- Before disrupting service, verify an independent remote recovery entry that remains usable without that platform, especially when the user is away. A second Agent on the same platform is not independent recovery. If no usable recovery route exists, prepare one within authorized scope or explain the blocker before proceeding.
- Preserve identities, sessions, data, previous binaries/images and service definitions. Inspect the effective service/runner environment, not just an interactive shell: executable paths, runtime capability probes, credentials mechanism and proxy settings. Validate the replacement through the actual service launch path; desktop application bundles may move their embedded CLI.
- Hand off disruptive steps to a bounded host-level process independent of the Agent session. Before cutover, prepare and verify its recovery commands, timeout, logs and failure notification. Restore known-good launch configuration/binaries on failed acceptance only when compatible; never automatically roll back a migrated database or overwrite newer user data. Do not create competing daemons or endless restart loops.
- Acceptance must cover server health, original Computer identity and connection, runtime discovery, and an authorized isolated Agent execution. A green doctor, connected Computer or database active flag alone does not prove Agent availability. Preserve intentionally stopped/deleted Agents; do not send unsolicited messages to real chats for testing.
- Record the recovery entry, acceptance results and remaining gaps in the system runbook. Clearly distinguish a documented recovery plan from an implemented and tested mechanism; never claim automatic recovery exists merely because this rule was added.

## macOS maintenance with Mole

When inspecting disk usage or performing requested Mac maintenance, check whether `mo` (Mole) is installed and use it where appropriate. On Fengye’s Mac Studio it is installed via Homebrew; verify locally rather than assuming it exists on other machines. `mo --version` and `mo --help` show the installed version and supported commands; `mo analyze` and `mo status` provide interactive disk and health views.

For cleanup, uninstall, project artifact purge, installer removal, app slimming, or system optimization, start with the relevant `mo <command> --dry-run` and review the exact scope, protected paths, and impact. `mo clean` may empty the user Trash, and clean/purge/installer can permanently delete files. Act only within the user’s requested scope, preserve unrelated files and services, and do not run broad cleanup, app removal, privilege changes, or optimization merely because Mole is installed. Consult the current upstream documentation for version-specific behavior; update Homebrew installations with Homebrew. Record durable installation or operational changes in the private runbook.

## Proxy Usage

Keep large-file downloads off Fengye's metered Clash proxy unless the user explicitly authorizes its use. Prefer direct access or a trustworthy download mirror, verifying the final redirect/CDN route and file integrity where available. Do not silently fall back to the paid proxy when direct access fails. Apply routing changes narrowly so normal proxied services remain available; keep machine-specific configuration in the network runbook.

## Required Documentation Sync

When a task produces durable personal-infrastructure information, update the runbook repository before finishing. This includes:

- host, network, service, runtime, version, address, startup, proxy, remote-access, backup, or recovery changes;
- domain, DNS, registrar, hosting, CDN/WAF, TLS, deployment, CI/CD, or public-service migrations;
- newly confirmed incidents, root causes, workarounds, pitfalls, architecture decisions, or validation results;
- installed or removed infrastructure software and external dependencies;
- configuration files or commands needed to reproduce or roll back a setup.

Reconcile the relevant runbook in place with the result, important paths, validation, and rollback boundary. Date only the facts actually checked; a documentation edit is not a fresh verification of the entire system. Add sanitized configuration copies under `configs/` when they materially aid recovery. Update the overview when roles, entry points, providers, or architecture change. If a new infrastructure category has no runbook yet, create an appropriately named runbook rather than forcing it into an unrelated machine document.

Then synchronize the private repository:

1. Review `git status` and stage only files belonging to the current work.
2. Run `git diff --cached --check` and inspect the staged diff for secrets.
3. Commit with a concise operational message.
4. Reconcile with `origin/main` without discarding work, then push to `origin/main`.
5. If authentication, conflicts, or remote availability prevent pushing, keep the local commit and clearly report what remains unsynchronized.

Documentation synchronization is expected for completed infrastructure work, but it does not grant permission for unrelated live-system changes.

## Keep Documentation Current

Maintain operating guidance, not an append-only conversation log. On every infrastructure task, tidy the sections you touch; perform a broader sweep when requested.

- Keep one canonical current statement per fact. Replace superseded setup steps, pending tasks and decisions; update affected indexes and cross-references rather than appending a contradictory “latest update”.
- Main runbooks retain current roles, entry points, essential configuration, operating constraints, diagnosis, backup and recovery. Put detailed timelines, resolved incidents and old measurements in `history/` with a warning and a link back to current guidance; link the archive from the main runbook. Never archive secrets.
- Resolve conflicts using live read-only evidence where available. Separate observed, configured, user-reported and reboot-tested facts with scoped dates. Correct disproven claims; label unverifiable facts and open questions explicitly instead of silently upgrading old notes to truth.
- Temporary experiments include their authoritative plan/data paths, end conditions and cleanup boundaries. Do not describe planned cleanup as completed or remove permanent services along with temporary jobs.
- Keep summaries short and task-oriented; avoid repeated status dumps, transient PIDs, transcripts and duplicate configuration. Preserve recovery commands and security invariants even when shortening prose. Keep machine-specific facts in runbooks, not this Skill.
- Before syncing, review the full diff, check internal links and contradictory/stale instructions, and preserve unrelated edits. Documentation cleanup alone never authorizes live service changes.

## Secret Boundary

Never commit or print passwords, SSH private keys, cookies, access or refresh tokens, API keys, proxy subscription URLs, node credentials, Raft login tokens, router sessions, RDP secrets, registrar recovery codes, encrypted credential payloads, or complete sensitive profiles. Record only the mechanism, owning system, sanitized path, and recovery procedure. Public keys, non-secret IDs, public/LAN/Tailscale addresses, versions, provider names, and redacted configuration examples may be documented when useful.

## Skill Source and Cross-Machine Installation

This Skill's only source of truth is `https://github.com/fengye404/fengye-skills`, normally cloned at `~/workspace/fengye-skills`. Do not duplicate the Skill inside the runbook repository. On a new machine, clone both private repositories and run `~/workspace/fengye-skills/install.sh`; the installer creates the tool-specific symlinks, while this Skill locates operational records in the runbook repository.

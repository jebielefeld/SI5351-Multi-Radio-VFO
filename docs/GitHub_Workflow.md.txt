# GitHub Workflow

# SI5351 Multi-Radio VFO Control Platform

---

# Overview

This project uses GitHub for:

- Source control
- Backup
- Version history
- Collaboration
- Installer releases
- Documentation management

GitHub Desktop is the recommended Git client.

---

# Core Workflow

Normal workflow:

```text
Edit
Commit
Push
```

---

# Definitions

## Edit

Modify source files using:

- VS Code
- Arduino IDE
- Notepad

---

## Commit

A commit creates a LOCAL engineering snapshot.

A commit does NOT upload changes to GitHub automatically.

Commits should describe logical engineering changes.

Examples:

```text
Added Output Manager
Implemented session restore
Fixed COM reconnect issue
Added RF safety monitor
```

---

## Push

Push uploads local commits to GitHub server.

After push:

- Local repository and GitHub server are synchronized
- GitHub online repository updates

---

# Recommended Commit Practices

Good commits are:

- Small
- Logical
- Descriptive
- Stable

Avoid huge mixed commits when possible.

---

# Recommended Workflow

1. Edit files
2. Test functionality
3. Verify stable operation
4. Commit locally
5. Push to GitHub

---

# IMPORTANT SAFETY RULE

Do not rely exclusively on GitHub as backup.

Also maintain:

- Local backups
- ZIP freeze snapshots
- Architecture reports

before major changes.

---

# Repository Visibility

Recommended workflow:

## Early Development

```text
Private repository
```

## Stable Public Release

```text
Public repository
```

after:

- cleanup
- documentation
- installer creation
- stable release validation

---

# Current Repository Structure

```text
firmware/
pc_software/
docs/
installer/
examples/
```

---

# Recommended Release Strategy

Recommended tagged releases:

```text
v4D6E Stable
v5.x
v6.x
```

Include:

- source code
- EXE installer
- user manual
- release notes

---

# Recommended Documentation

Important documentation files:

```text
README.md
CHATGPT_REBUILD_REPORT.md
```

The rebuild report acts as long-term architecture continuity documentation.

---

# Recommended ChatGPT Start Command

```text
Continue SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE

Use CHATGPT_REBUILD_REPORT.md as primary architecture reference.
```
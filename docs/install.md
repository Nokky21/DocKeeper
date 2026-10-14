# Installing DocKeeper

[← README](../README.md) · [Reference](reference.md) · [Architecture](architecture.md)

The repository root **is** the skill folder. Clone it into a folder named exactly `dockeeper`: the
Agent Skills standard requires the folder name to match the skill name. Requirements: `python3`
(3.10+) and `git`. <!-- dockeeper: .github/workflows/ci.yml:20 -->

**Claude Code** (terminal, desktop app, VS Code or JetBrains):

```bash
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper
```

**Codex, Gemini CLI, Cursor, GitHub Copilot / VS Code** (all of them read `~/.agents/skills`):

```bash
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

**One project only** (commit it so the whole team gets it): run the same `git clone` into
`.claude/skills/dockeeper` or `.agents/skills/dockeeper` inside that repository.

**No agent** (by hand, git hook or CI): clone it anywhere and run `python3 <folder>/bin/dockeeper`.
<!-- dockeeper: bin/dockeeper:7 -->

## Paths by agent

Where each tool looks for skills, according to its own documentation. Clone into any one of the
listed folders.

| Agent | All your projects | One project | Docs |
|---|---|---|---|
| Claude Code | `~/.claude/skills/dockeeper` | `.claude/skills/dockeeper` | [skills](https://code.claude.com/docs/en/skills) |
| Codex | `~/.agents/skills/dockeeper` | `.agents/skills/dockeeper` | [skills](https://developers.openai.com/codex/skills/) |
| Gemini CLI | `~/.gemini/skills/dockeeper` or `~/.agents/skills/dockeeper` | `.gemini/skills/dockeeper` or `.agents/skills/dockeeper` | [skills](https://geminicli.com/docs/cli/skills/) |
| Cursor | `~/.cursor/skills/dockeeper`, `~/.agents/skills/dockeeper` (also reads `~/.claude/skills`) | `.cursor/skills/dockeeper` or `.agents/skills/dockeeper` | [skills](https://cursor.com/docs/context/skills) |
| GitHub Copilot / VS Code | `~/.copilot/skills/dockeeper`, `~/.agents/skills/dockeeper` (also reads `~/.claude/skills`) | `.github/skills/dockeeper`, `.agents/skills/dockeeper` or `.claude/skills/dockeeper` | [skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills) |
| Other Agent Skills clients | see their docs | see their docs | [client list](https://agentskills.io) |

## Windows

Same folders under your user profile (`%USERPROFILE%`, `$env:USERPROFILE` in PowerShell). Use
`python` if `python3` is not on your `PATH`.

| Agent | Folder |
|---|---|
| Claude Code | `%USERPROFILE%\.claude\skills\dockeeper` |
| Codex, Gemini CLI, Cursor, Copilot | `%USERPROFILE%\.agents\skills\dockeeper` |

```powershell
git clone https://github.com/Nokky21/DocKeeper.git "$env:USERPROFILE\.claude\skills\dockeeper"
python "$env:USERPROFILE\.claude\skills\dockeeper\bin\dockeeper" --version
```

## Update and uninstall

- Update: `git -C ~/.claude/skills/dockeeper pull` (use the folder you cloned into).
- Uninstall: delete that folder. Nothing else is installed anywhere. <!-- dockeeper: bin/dockeeper:7 -->

## claude.ai, the Claude API and the Agent SDK

- **claude.ai (web or desktop chat).** Download `dockeeper-skill.zip` from the
  [latest release](https://github.com/Nokky21/DocKeeper/releases/latest) and upload it in the Skills
  section of your settings (code execution must be enabled). Be aware of the limit: a chat sandbox
  does not have your repository or its git history, and the seal file would not persist. It is fine
  for drafting documentation, not for keeping it verified. Use a coding agent or CI for that.
  <!-- dockeeper: .github/workflows/release.yml:28 -->
- **Claude Agent SDK.** It reads the same `~/.claude/skills` and `.claude/skills` folders as Claude
  Code. See the [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
- **Claude API.** Custom skills are uploaded through the Skills API and run with the code execution
  tool; the same limits as claude.ai apply. See the
  [skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

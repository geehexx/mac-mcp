# Cline Rules & Workflows for MAC MCP

This directory contains comprehensive Cline configuration including rules, hooks, workflows, and prompts to enable advanced AI-assisted development.

## Directory Structure

```
.clinerules/
├── README.md              # This file
├── rules/                 # Core rules and patterns
│   ├── core/              # Core development workflows
│   └── reference/         # Reference patterns and guidelines
├── hooks/                 # Cline hooks for automation
├── workflows/             # Reusable workflow templates
├── prompts/               # Prompt templates and libraries
├── agents/                # Agent configuration
└── subagents/             # Sub-agent definitions
```

## Features Enabled

### 1. **Hooks System** (Experimental)
Automated quality gates and context injection at key workflow points.

**Status**: ✅ Enabled (requires manual activation in Cline settings)

**Available Hooks**:
- `TaskStart` - Initialize context when starting tasks
- `PreToolUse` - Validate operations before execution
- `PostToolUse` - Learn from completed operations
- `UserPromptSubmit` - Inject context based on user input

### 2. **Expert Review Panel Protocol**
Multi-agent debate system for improved decision-making.

**When to Use**: Before implementation, every 200+ lines, before commit, for complex decisions

### 3. **Workflows**
Reusable workflow templates for common tasks.

**Usage**: Type `/workflow-name.md` in Cline chat

### 4. **Sub-Agent Orchestration**
Delegate research and exploration to focused Cline instances using CLI.

**Usage**: `cline "your focused research prompt"`

### 5. **Comprehensive Rules**
Advanced development workflows, quality procedures, and coding patterns.

## Manual Activation Steps

### Enable Hooks (Required)

1. Open Cline Settings (click Settings button in Cline panel)
2. Navigate to "Features" section
3. Check "Enable Hooks" checkbox
4. Restart VSCode if needed

### Verify Hook Execution

Hooks are stored in `.clinerules/hooks/` and must be:
- Executable: `chmod +x .clinerules/hooks/*`
- Have shebang: `#!/usr/bin/env bash` or `#!/usr/bin/env python3`
- Output valid JSON to stdout

### Enable Sub-Agents via CLI

The Cline CLI tool must be installed:

```bash
npm install -g @cline/cli
```

Or if using the VSCode extension's built-in CLI, it's automatically available.

## Quick Start

1. **Enable hooks** in Cline settings (see above)
2. **Make hooks executable**:
   ```bash
   chmod +x .clinerules/hooks/*
   ```
3. **Start a task** - TaskStart hook will inject initial context
4. **Use workflows** - Type `/` in chat to see available workflows
5. **Delegate research** - Use `cline "research prompt"` for exploration

## Documentation

- **Core Workflows**: `.clinerules/rules/core/development-workflow.md`
- **Expert Review Panel**: `.clinerules/rules/core/expert-review-panel.md`
- **Quality Procedures**: `.clinerules/rules/core/quality-procedures.md`
- **Code Patterns**: `.clinerules/rules/reference/code-patterns.md`

## Advanced Features

### Dynamic Expert Protocol

Automatically convene expert panels for complex decisions. See `rules/core/expert-review-panel.md` for details.

### Context Management

Uses Claude Sonnet 4.5 with 200K context window via Bedrock. Can be extended to 1M context for advanced workflows.

### Quality Gates

Pre-commit hooks integrate with Cline hooks to enforce:
- Code formatting (ruff)
- Type checking (mypy)
- Test coverage (pytest)
- Event immutability validation
- Async pattern validation

## Troubleshooting

### Hooks Not Running

- Verify "Enable Hooks" is checked in settings
- Check hooks are executable: `ls -l .clinerules/hooks/`
- Verify shebang line in hook files
- Check VSCode Output panel (Cline channel) for errors

### Workflows Not Appearing

- Workflows must be in `.clinerules/workflows/` directory
- Must have `.md` extension
- Invoke with `/workflow-name.md` in chat

### Sub-Agents Not Working

- Verify Cline CLI is installed: `which cline` or `cline --version`
- Check you're in a VSCode workspace
- Try with simple prompt first: `cline "list all .py files"`

## Integration with Existing Config

This setup enhances but does not replace:
- `pyproject.toml` - Python dependencies and tool configuration
- `.pre-commit-config.yaml` - Git pre-commit hooks
- `config.yaml` - MAC MCP runtime configuration

The old `.clinerules` file has been backed up to `.clinerules.backup`.

## Contributing

When adding new rules, workflows, or hooks:
1. Follow existing patterns and structure
2. Document in this README
3. Test thoroughly before committing
4. Update relevant documentation

## Learn More

- [Cline Hooks Documentation](https://docs.cline.bot/features/hooks)
- [Cline Workflows](https://docs.cline.bot/features/slash-commands/workflows)
- [Cline CLI](https://docs.cline.bot/cline-cli/overview)
- [Expert Review Panel Research](https://arxiv.org/abs/2402.XXXXX) (multi-agent debate)

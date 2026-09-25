# Evidence package skills

Two Agent Skills for investigations that need a traceable evidence record:

| Skill | Purpose |
| --- | --- |
| `evidence-package-producer` | Capture source results as evidence nodes during an investigation and assemble a verifiable JSON package. |
| `evidence-package-handoff` | Turn that package into a short briefing and continue the same evidence graph as new findings arrive. |

Each skill has its own `SKILL.md` under [`skills/`](skills/). They can be installed together or separately.

## Install

Install from the public GitHub repository:

```sh
npx skills add shadrus/evidence-package --list
npx skills add shadrus/evidence-package --skill evidence-package-producer --skill evidence-package-handoff
```

The first command shows the skills the CLI discovers. The second installs both. To install one, pass only its `--skill` option.

## Use

Ask for a verifiable evidence package when starting an investigation. Give the resulting JSON package to `evidence-package-handoff` for a concise briefing or follow-up investigation. The handoff skill continues the original `e1`, `e2`, … node sequence when adding findings.

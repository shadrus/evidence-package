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

## Update

After changes are pushed to this repository, people who already installed the skills can fetch the latest versions from their install location:

```sh
npx skills list
npx skills update evidence-package-producer evidence-package-handoff
```

Add `-g` to `update` for a global installation. Updates are run by each user; pushing a commit does not change their installed copy automatically.

## Remove

```sh
npx skills remove evidence-package-producer evidence-package-handoff
```

Pass only one name to remove one skill. Add `-g` for a global installation. Removing a skill from this repository does not remove existing installations.

## Find

Search the skills catalog by skill name and GitHub owner:

```sh
npx skills find evidence-package-producer --owner shadrus
npx skills find evidence-package-handoff --owner shadrus
```

Catalog search depends on installation telemetry and may take time to show a new repository. `npx skills add shadrus/evidence-package --list` reads this repository directly and works independently of catalog indexing.

## Use

Ask for a verifiable evidence package when starting an investigation. Give the resulting JSON package to `evidence-package-handoff` for a concise briefing or follow-up investigation. The handoff skill continues the original `e1`, `e2`, … node sequence when adding findings.

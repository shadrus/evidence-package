# Evidence package skills

Three Agent Skills for investigations that need a traceable evidence record:

| Skill                       | Purpose                                                                                                  |
| --------------------------- | -------------------------------------------------------------------------------------------------------- |
| `evidence-package-producer` | Capture source results as evidence nodes during an investigation and assemble a verifiable JSON package. |
| `evidence-package-handoff`  | Turn that package into a short briefing and continue the same evidence graph as new findings arrive.     |
| `evidence-package-publish`  | Publish a JSON package on explicit request and return a share link.                                      |

Each skill has its own `SKILL.md` under [`skills/`](skills/). They can be installed together or separately.

## Install

Install from the public GitHub repository:

```sh
npx skills add shadrus/evidence-package --list
npx skills add shadrus/evidence-package --skill evidence-package-producer --skill evidence-package-handoff --skill evidence-package-publish
```

The first command shows the skills the CLI discovers. The second installs both. To install one, pass only its `--skill` option.

## Update

After changes are pushed to this repository, people who already installed the skills can fetch the latest versions from their install location:

```sh
npx skills list
npx skills update evidence-package-producer evidence-package-handoff evidence-package-publish
```

Add `-g` to `update` for a global installation. Updates are run by each user; pushing a commit does not change their installed copy automatically.

## Remove

```sh
npx skills remove evidence-package-producer evidence-package-handoff evidence-package-publish
```

Pass only one name to remove one skill. Add `-g` for a global installation. Removing a skill from this repository does not remove existing installations.

## Find

Search the skills catalog by skill name and GitHub owner:

```sh
npx skills find evidence-package-producer --owner shadrus
npx skills find evidence-package-handoff --owner shadrus
npx skills find evidence-package-publish --owner shadrus
```

Catalog search depends on installation telemetry and may take time to show a new repository. `npx skills add shadrus/evidence-package --list` reads this repository directly and works independently of catalog indexing.

## Use

Ask for a verifiable evidence package when starting an investigation. Give the resulting JSON package or its published share link to `evidence-package-handoff` for a concise briefing or follow-up investigation. The handoff skill continues the original `e1`, `e2`, … node sequence when adding findings.

To publish, ask explicitly for a share link. Configure the publisher once in your own terminal using the API origin of the public service instance:

```sh
python3 skills/evidence-package-publish/scripts/publish.py configure --base-url https://api.aiproof.site360.tech
```

The command prompts for an optional API key without echoing it and stores it locally with user-only file permissions. Leave the key blank for an anonymous link that expires after seven days. The service runs at [aiproof.site360.tech](https://aiproof.site360.tech) (API at `api.aiproof.site360.tech`); account sign-in and keys are being developed separately.

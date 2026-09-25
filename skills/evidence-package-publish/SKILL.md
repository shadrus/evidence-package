---
name: evidence-package-publish
description: Publish an evidence package JSON file to an evidence-package service when the user explicitly asks for a share link. Supports anonymous publication or a locally configured API key.
---

# Publish an evidence package

Publish only after the user explicitly requests publication. Find the JSON
package they named and use `scripts/publish.py publish <path>` from this skill's
directory. The command prints the share URL. Return that URL and the expiration
reported by the service. Each upload creates a new, independent publication.

The helper reads its service URL and optional API key from a local config file.
If it is not configured, tell the user to run this command with the API origin
in their own terminal:

```sh
python3 scripts/publish.py configure --base-url https://API-ORIGIN
```

The command asks for the API key with hidden input. Leaving it blank configures
anonymous publication, which expires after seven days. A signed-in user creates
their key in the service UI and pastes it once into the local command. Handle the
key as a secret: have the user enter it in their own terminal, never in chat.

By default the service adds rich chat-preview metadata containing the author's
conclusion. Pass `--no-preview` only when the user explicitly requests no rich
preview. The helper sends the package's original JSON bytes and checks the
SHA-256 returned by the service.

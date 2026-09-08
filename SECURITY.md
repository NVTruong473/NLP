# Security

## API keys

Never commit `providers.env`.

A public GitHub repository cannot contain a file that is visible only to the repository owner. If a secret is committed to a public branch, assume it has been copied even if the commit is later deleted.

This repository therefore commits only `providers.env.example` and ignores:

```text
providers.env
*.env
```

## Google Colab

The recommended workflow is:

1. keep `providers.env` on your own computer or private Google Drive;
2. run the Colab notebook;
3. the notebook checks `/content/providers.env`;
4. if it is absent, upload it into the temporary Colab runtime;
5. keys are loaded into environment variables and their values are never printed.

Colab runtime storage is temporary. Re-upload after a runtime reset, or keep the file in a private Google Drive location.

## If a key was exposed

Revoke/rotate it immediately in the provider dashboard. Creating a new Git commit that removes the key is **not** sufficient, because the old value remains in Git history and may already have been indexed or copied.

## Private documents

`data/uploads/`, `data/private/`, and generated `artifacts/` are Git-ignored. Review `git status` before every push when using real institutional data.

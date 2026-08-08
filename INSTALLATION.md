# Installation

Install `confirm-with-pseudocode` as a **directory**, not as a standalone
`SKILL.md` file.

The current runtime package includes required subdirectories and a local PDL
reference. A partial installation can appear to work until the skill tries to
load that reference, so installation is complete only after the runtime
manifest verifier passes against the installed directory.

## Recommended: ask an agent to install and verify it

Give an agent with filesystem and shell access this prompt:

```text
Install the confirm-with-pseudocode skill from
https://github.com/paragon-ux/PDL-Standard.

Requirements:
1. Acquire the repository or an archive into a temporary/local source directory.
2. Install the entire confirm-with-pseudocode/ directory recursively into this
   host's local skills directory. Do not install only SKILL.md.
3. Preserve the package subdirectories and content. Do not rewrite files during installation.
4. Before using the skill, run the repository's deterministic verifier:

   python scripts/verify_runtime_manifest.py --root <installed-skill-directory>

5. The installation is successful only if it reports RUNTIME MANIFEST PASS.
6. If the verifier cannot run or any required file is missing/mismatched, stop
   and report the installation as incomplete; do not fetch a runtime substitute
   for a missing skill reference.
7. Report the exact installed directory and verifier result.
```

This wording is intentionally explicit about recursive package installation and
post-copy verification. A host's generic "install skill from URL" action is not
sufficient evidence that nested files were copied.

## Safe manual installation

### 1. Materialize the repository locally

Use either a normal Git clone or GitHub's **Download ZIP** action. Do not copy a
raw `SKILL.md` URL by itself.

Git example:

```bash
git clone --depth 1 https://github.com/paragon-ux/PDL-Standard.git
cd PDL-Standard
```

### 2. Verify the source package

From the repository root:

```bash
python scripts/verify_runtime_manifest.py
```

Expected first line:

```text
RUNTIME MANIFEST PASS
```

You can also run the verifier's failure-mode tests:

```bash
python scripts/verify_runtime_manifest.py --self-test
```

### 3. Copy the complete directory

#### Codex / PowerShell

If `CODEX_HOME` is configured:

```powershell
$source = Resolve-Path .\confirm-with-pseudocode
$target = Join-Path $env:CODEX_HOME 'skills\confirm-with-pseudocode'
if (Test-Path -LiteralPath $target) {
    throw "Target already exists. Move or remove the old installation intentionally before copying."
}
Copy-Item -LiteralPath $source -Destination $target -Recurse
python .\scripts\verify_runtime_manifest.py --root $target
```

If the destination already exists and contains undeclared files, the verifier
will fail exact-tree validation. Remove or archive the old skill directory only
when you intend to replace that installation, then perform a fresh recursive
copy.

#### POSIX shell

Set the destination for your agent host, then copy the directory as a unit:

```bash
SOURCE="$(pwd)/confirm-with-pseudocode"
TARGET="${CODEX_HOME}/skills/confirm-with-pseudocode"
mkdir -p "$(dirname "$TARGET")"
if [ -e "$TARGET" ]; then
  echo "Target already exists; move or remove it intentionally before copying." >&2
  exit 1
fi
cp -R "$SOURCE" "$TARGET"
python scripts/verify_runtime_manifest.py --root "$TARGET"
```

If your host uses a different skills location, substitute that directory.

### 4. Start a new conversation/session

Skill discovery is commonly initialized at session start. After verification,
start a new session if your host does not automatically refresh installed
skills.

Then invoke it explicitly, for example:

```text
Use $confirm-with-pseudocode to compare PostgreSQL and SQLite for an offline
application. Prioritize simple deployment, exclude managed services, and end
with a recommendation for a three-person team.
```

## What the verifier proves

The current runtime manifest verifier mechanically checks:

- the package directory exists;
- required `agents/` and `references/` directories exist;
- every declared runtime file exists;
- installed content matches the reviewed Git blob digests under each file's declared EOL normalization; and
- no undeclared substantive package files are present.

It does **not** judge whether Prompt Pseudocode is semantically correct, whether
a Response Plan is appropriate, or whether final execution follows the user's
meaning. Those are separate semantic/human assurance concerns described in the
architecture documents.

## Troubleshooting

### `references/pdl-conventions.md` is missing

The installation is incomplete. Reinstall the complete directory and rerun the
manifest verifier. Do not compensate by fetching the Cal Poly source during
skill execution; the runtime is designed to use its local project-authored
compatibility profile.

### Digest mismatch

The installed bytes differ from the reviewed repository package. Re-copy the
package from the same repository revision or intentionally update
`runtime-manifest.json` as part of a reviewed runtime change.

### Unexpected file

The current manifest uses an exact runtime file set. If an old installation
contains extra substantive files, install into a clean target directory or
review the package change and update the manifest intentionally.

### Python is unavailable

Do not describe the installation as mechanically verified. You can still
inspect the required files manually, but the deterministic package-integrity
claim requires running the verifier or an equivalent implementation of the same
manifest checks.

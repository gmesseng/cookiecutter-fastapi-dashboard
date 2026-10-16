"""
Post-génération :
  1. retire les blocs optionnels (CI GitHub, ETL et sa page de doc) selon les réponses ;
  2. crée le .env à partir de .env.example avec une SECRET_KEY aléatoire ;
  3. initialise git et installe les hooks de conformité (commit-msg, pre-push).
"""
import os
import secrets
import shutil
import stat
import subprocess

CI_TOOL = "{{ cookiecutter.ci_tool }}"
INCLUDE_ETL = "{{ cookiecutter.include_etl }}".lower().startswith("y")
INIT_GIT = "{{ cookiecutter.init_git }}".lower().startswith("y")
ENV_PREFIX = "{{ cookiecutter.env_prefix }}"

# Messages de commit : "[type]: message" (les merges et reverts générés par git sont tolérés).
COMMIT_MSG_HOOK = r"""#!/bin/sh
# Refuse les messages de commit non conformes : [type]: message
pattern='^\[(feat|fix|docs|style|refactor|test|chore)\]: .+'
first_line=$(head -n 1 "$1")
case "$first_line" in
    Merge\ *|Revert\ *) exit 0 ;;
esac
if ! echo "$first_line" | grep -Eq "$pattern"; then
    echo "Message de commit non conforme : '$first_line'"
    echo "Format attendu : [feat|fix|docs|style|refactor|test|chore]: message"
    exit 1
fi
"""

# Tags : vX.Y.Z, le format lu par .github/scripts/get-version.sh.
PRE_PUSH_HOOK = r"""#!/bin/sh
# Refuse le push de tags non conformes (format attendu : vX.Y.Z)
pattern='^v[0-9]+\.[0-9]+\.[0-9]+$'
while read -r local_ref local_sha remote_ref remote_sha; do
    case "$remote_ref" in
        refs/tags/*)
            tag="${remote_ref#refs/tags/}"
            if ! echo "$tag" | grep -Eq "$pattern"; then
                echo "Tag non conforme : '$tag' (format attendu : vX.Y.Z)"
                exit 1
            fi
            ;;
    esac
done
exit 0
"""


def remove_optional_parts() -> None:
    if CI_TOOL != "GitHub":
        shutil.rmtree(".github", ignore_errors=True)
    if not INCLUDE_ETL:
        shutil.rmtree("etl", ignore_errors=True)
        shutil.rmtree("db", ignore_errors=True)
        os.remove(os.path.join("docs", "docs", "etl.md"))


def create_env_file() -> None:
    if os.path.exists(".env"):
        return
    with open(".env.example", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(
        f"{ENV_PREFIX}SECRET_KEY=generate_a_secure_key_here_never_commit_the_real_one",
        f"{ENV_PREFIX}SECRET_KEY={secrets.token_urlsafe(48)}",
    )
    with open(".env", "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(".env créé à partir de .env.example (SECRET_KEY générée) — renseigner les URI PostgreSQL.")


def install_git_hooks() -> None:
    if shutil.which("git") is None:
        print("git introuvable : initialisation du dépôt et hooks ignorés.")
        return
    subprocess.run(["git", "init", "--quiet"], check=True)
    hooks_dir = os.path.join(".git", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    for name, content in (("commit-msg", COMMIT_MSG_HOOK), ("pre-push", PRE_PUSH_HOOK)):
        path = os.path.join(hooks_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print("Dépôt git initialisé, hooks commit-msg et pre-push installés.")


def main() -> None:
    remove_optional_parts()
    create_env_file()
    if INIT_GIT:
        install_git_hooks()
    print("\nProjet {{ cookiecutter.project_slug }} généré. Prochaines étapes : voir README.md.")


if __name__ == "__main__":
    main()

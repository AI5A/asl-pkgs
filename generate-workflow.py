#!/usr/bin/env python3

# This script generates a workflow file for the GitHub Actions CI.
import yaml

ARTIFACTS = [
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bullseye-x86_64"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-buster-x86_64"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bullseye-armv7l"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-buster-armv7l"),
    ("AI5A/asl", "fixes", "allstarlink-bullseye-x86_64"),
    ("AI5A/asl", "fixes", "allstarlink-buster-x86_64"),
    ("AI5A/asl", "fixes", "allstarlink-bullseye-armv7l"),
    ("AI5A/asl", "fixes", "allstarlink-buster-armv7l"),
    # These two are noarch, so we just use the armv7l ones
    ("AI5A/asl-update-node-list", "fixes", "asl-update-node-list-bullseye"),
    ("AI5A/asl-update-node-list", "fixes", "asl-update-node-list-buster"),
]
PKGS = ["asl-dahdi", "asl", "asl-update-node-list"]

debian_versions = set(
    x[2].split("-")[-2] for x in ARTIFACTS if "update-node-list" not in x[2]
)
arch_map = {
    "x86_64": "amd64",
    "armv7l": "armhf",
}
# Script to move the files into the deb repo hierarchy
MOVE_DEBS = f"""
repo="$(pwd)"
for codename in {' '.join(debian_versions)}; do
    # Create pool directory
    mkdir -p asl-pkgs/deb/$codename/pool/main/
    # Move the debs
    pushd asl-pkgs/deb/$codename/pool/main/
    for pkg in {' '.join(PKGS)}; do
        mv -v "$repo/$pkg-$codename"-*/*
    done
    popd

    # Create dist hierarchy
    pushd asl-pkgs/deb/$codename/
    for arch in {' '.join(arch_map.values())}; do
        mkdir -p dists/$codename/main/binary-$arch/
        dpkg-scanpackages --arch $arch pool/main/ | gzip -9c > dists/$codename/main/binary-$arch/Packages.gz
    done
    popd

    # Create Release file
    pushd asl-pkgs/deb/$codename/
      bash $repo/generate-release.sh $codename > Release
      gpg --armour --sign --detach-sign --output Release.gpg Release
    popd
done
"""

GENERATE_INDEXES = """
curl -o gen-indexes.py https://raw.githubusercontent.com/relrod/oneoff/master/generate-html-indexes.py
find asl-pkgs > files-list.txt
cat files-list.txt
cat files-list.txt | python3 gen-indexes.py .
tree .
"""


def generate_workflow():
    artifact_steps = []
    for repo, branch, artifact in ARTIFACTS:
        artifact_steps.append(
            {
                "name": f"Download {artifact}",
                "uses": "dawidd6/action-download-artifact@v2",
                "with": {
                    "github_token": "${{ secrets.GITHUB_TOKEN }}",
                    "workflow": f'build-{"x86" if "x86" in artifact else "arm"}.yml',
                    "name": artifact,
                    "path": artifact,
                    "repo": repo,
                    "branch": branch,
                    "workflow_conclusion": "success",
                },
            }
        )

    workflow = {
        "name": "Generate deb repository",
        "on": {
            "push": {},
            "workflow_dispatch": {},
        },
        "jobs": {
            "generate-deb-repository": {
                "name": "Generate deb repository",
                "runs-on": "ubuntu-latest",
                "timeout-minutes": 15,
                "strategy": {
                    "fail-fast": False,
                },
                "steps": [
                    {
                        "name": "Checkout",
                        "uses": "actions/checkout@v2",
                    },
                    *artifact_steps,
                    {
                        "name": "Import GPG key",
                        "uses": "crazy-max/ghaction-import-gpg@v5",
                        "with": {
                            "gpg_private_key": "${{ secrets.GPG_SECRET_KEY }}",
                            "passphrase": "${{ secrets.GPG_PASSPHRASE }}",
                        },
                    },
                    {
                        "name": "Install dependencies",
                        "run": "sudo apt-get install -y gcc dpkg-dev gpg",
                    },
                    {
                        "name": "Move debs",
                        "run": MOVE_DEBS,
                    },
                    {
                        "name": "Generate indexes",
                        "run": GENERATE_INDEXES,
                    },
                    {
                        "name": "Push to GitHub Pages",
                        "uses": "JamesIves/github-pages-deploy-action@v4",
                        "with": {
                            "folder": "asl-pkgs",
                            "clean": False,
                        },
                    },
                ],
            },
        },
    }
    return workflow


if __name__ == "__main__":
    print("# NOTE: This file is generated by generate-workflow.py")
    print("# Do not edit this file directly.")
    print()
    print(yaml.dump(generate_workflow(), sort_keys=False))
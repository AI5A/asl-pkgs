#!/usr/bin/env python3

# This script generates a workflow file for the GitHub Actions CI.
import yaml

ARTIFACTS = [
    # x86
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bookworm-x86_64", "build-x86.yml"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bullseye-x86_64", "build-x86.yml"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-buster-x86_64", "build-x86.yml"),

    # arm
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bookworm-armv7l", "build-arm.yml"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-bullseye-armv7l", "build-arm.yml"),
    ("AI5A/asl-dahdi", "fixes", "asl-dahdi-buster-armv7l", "build-arm.yml"),

    # x86
    ("AI5A/asl", "fixes", "allstarlink-bookworm-x86_64", "build-x86.yml"),
    ("AI5A/asl", "fixes", "allstarlink-bullseye-x86_64", "build-x86.yml"),
    ("AI5A/asl", "fixes", "allstarlink-buster-x86_64", "build-x86.yml"),

    # arm
    ("AI5A/asl", "fixes", "allstarlink-bookworm-armv7l", "build-arm.yml"),
    ("AI5A/asl", "fixes", "allstarlink-bullseye-armv7l", "build-arm.yml"),
    ("AI5A/asl", "fixes", "allstarlink-buster-armv7l", "build-arm.yml"),

    # These are noarch, so we don't duplicate them
    ("AI5A/asl-update-node-list", "fixes", "asl-update-node-list-bookworm", "build.yml"),
    ("AI5A/asl-update-node-list", "fixes", "asl-update-node-list-bullseye", "build.yml"),
    ("AI5A/asl-update-node-list", "fixes", "asl-update-node-list-buster", "build.yml"),
]
PKGS = ["asl-dahdi", "allstarlink", "asl-update-node-list"]

debian_versions = list(set(
    x[2].split("-")[-2] for x in ARTIFACTS if "update-node-list" not in x[2]
))
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
        for file in $repo/$pkg-$codename*/*.deb; do
            mv -v $file .
        done
    done
    popd

    # Create dist hierarchy
    pushd asl-pkgs/deb/$codename/
    for arch in {' '.join(arch_map.values())}; do
        mkdir -p dists/$codename/main/binary-$arch/
        dpkg-scanpackages --arch $arch pool/main/ > dists/$codename/main/binary-$arch/Packages
    done
    popd

    # Create Release file
    pushd asl-pkgs/deb/$codename/dists/$codename/
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
    for repo, branch, artifact, workflow in ARTIFACTS:
        artifact_steps.append(
            {
                "name": f"Download {artifact}",
                "uses": "dawidd6/action-download-artifact@v2",
                "with": {
                    "github_token": "${{ secrets.GITHUB_TOKEN }}",
                    "workflow": workflow,
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
                        "name": "Sync repository",
                        "uses": "jakejarvis/s3-sync-action@master",
                        "env": {
                            "AWS_S3_BUCKET": "repo-ai5a-net",
                            "AWS_ACCESS_KEY_ID": "${{ secrets.B2_KEY_ID }}",
                            "AWS_SECRET_ACCESS_KEY": "${{ secrets.B2_APPLICATION_KEY }}",
                            "AWS_S3_ENDPOINT": "https://s3.us-west-000.backblazeb2.com/",
                            "SOURCE_DIR": "asl-pkgs",
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

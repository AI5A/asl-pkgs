# AllStarLink packages

TODO: Explain build process

TLDR:
- https://github.com/ai5a/asl
- https://github.com/ai5a/asl-dahdi
- https://github.com/ai5a/asl-update-node-list

These build .deb files on GitHub Actions in an ARM VM.

This repository (asl-pkgs) takes all of the output from those repos
and turns it into a Debian repo (possibly also an RPM repo later on) that
people can use.

## Debian Repository

```bash
# Grab GPG public key
curl -o /etc/apt/trusted.gpg.d/ai5a-asl.asc \
  https://raw.githubusercontent.com/AI5A/asl-pkgs/main/pkg_pub_key.asc

# Set up the actual repo source
echo "deb [signed-by=/etc/apt/trusted.gpg.d/ai5a-asl.asc] https://repo.ai5a.net/asl-pkgs/deb/$(grep VERSION_CODENAME /etc/os-release | cut -d= -f2) $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2) main" \
  > /etc/apt/sources.list.d/ai5a-asl.list
```

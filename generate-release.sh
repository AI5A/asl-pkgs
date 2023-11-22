#!/usr/bin/env bash
set -e

# from https://earthly.dev/blog/creating-and-hosting-your-own-deb-packages-and-apt-repo/

do_hash() {
    HASH_NAME=$1
    HASH_CMD=$2
    echo "${HASH_NAME}:"
    for f in $(find -type f); do
        f=$(echo $f | cut -c3-) # remove ./ prefix
        if [ "$f" = "Release" ]; then
            continue
        fi
        echo " $(${HASH_CMD} ${f}  | cut -d" " -f1) $(wc -c $f)"
    done
}

cat <<EOF
Suite: stable
Codename: $1
Version: 1.0
Architectures: amd64 armhf
Components: main
Description: AI5A AllStarLink Debian Repository
Date: $(date -Ru)
EOF
do_hash "MD5Sum" "md5sum"
do_hash "SHA1" "sha1sum"
do_hash "SHA256" "sha256sum"

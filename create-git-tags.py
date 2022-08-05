#!/usr/bin/env python3

import argparse
import json
import logging
import os
import requests
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

parser = argparse.ArgumentParser(
    description="Create a Git tag to a remote commit, after a successful ROCK build."
)
parser.add_argument(
    "--token",
    dest="token",
    required=True,
    help="authz token for organization-wide read operations",
)
parser.add_argument(
    "--marked-for-publishing",
    dest="marked_for_publishing",
    required=True,
    help="path to the file where the published ROCKs have been listed",
)
parser.add_argument("--branch", dest="branch", required=True, help="remote branch name")
parser.add_argument("--risk", dest="risk", required=True, help="build risk")
parser.add_argument(
    "--commit", dest="commit", required=True, help="sha of the remote commit"
)
parser.add_argument(
    "--rock-repository",
    dest="rock_repository",
    required=True,
    help="ubuntu-rocks/<repo> of the ROCK project",
)

args = parser.parse_args()

headers = {
    "Authorization": f"token {args.token}",
    "Accept": "application/vnd.github+json",
}

with open(args.marked_for_publishing) as pub:
    published = pub.readlines()

tag_prefix = "/".join(args.branch.split("/")[:2])
all_tags = []
for rock in published:
    _, rock_name, rock_version, rock_base, _, rock_revision, oci_tags = rock.split(",")
    tag_name = f"{tag_prefix}/{rock_name}/{rock_version}/{rock_base}/{rock_revision}/{args.risk}"
    tag_payload = {
        "tag": tag_name,
        "message": f"New revision {rock_revision} of {rock_name} {rock_version} created (OCI tags: {oci_tags})",
        "object": args.commit,
        "type": "commit",
        "tagger": {
            "name": os.environ["GITHUB_ACTOR"],
            "email": "rocks-dev@lists.canonical.com",
        },
    }

    create_tag_url = f"{os.environ['GITHUB_API_URL']}/repos/{args.rock_repository}/git/tags"
    tag = requests.post(
        create_tag_url, headers=headers, data=json.dumps(tag_payload)
    ).json()

    logging.info(f"Git tag {tag_name} creation response: {tag}")

    ref_url = f"{os.environ['GITHUB_API_URL']}/repos/{args.rock_repository}/git/refs"
    ref_payload = {"ref": f"refs/tag/{tag_name}", "sha": tag["sha"]}
    ref = requests.post(ref_url, headers=headers, data=json.dumps(ref_payload))
    ref.raise_for_status()
    all_tags.append(tag_name)

print(f"::set-output name=git-tags::{', '.join(all_tags)}")

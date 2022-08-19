#!/usr/bin/env python3

"""Scans all repositories, looking for tags with the following
naming convention:
  release/<rock>/<revision>/<targetTrack>/<targetRisk>
  
If there are any of these tags, without an associated GitHub release, 
then release and re-tag (OCI) that ROCK."""

import logging
import os
import re
import requests
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from helper_functions import get_all_pages, check_org_argparse, list_rocks_projects

ORG = "ubuntu-rocks"
GIT_API_URL = "https://api.github.com"


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = check_org_argparse(
        "Scan the ubuntu-rocks GitHub organization, finding which ROCK repos asking for releases to be made."
    )
    args = parser.parse_args()

    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github+json",
    }

    rocks_projects, exclude_repos = list_rocks_projects(
        GIT_API_URL, ORG, headers, args.on_repo
    )

    new_release_tags = []
    for rock in rocks_projects:
        if rock["name"] in exclude_repos:
            continue

        logging.info(f"Scanning new release requests in {rock['name']} project...")
        # Get all tags
        url = f"{GIT_API_URL}/repos/{ORG}/{rock['name']}/tags"
        all_rock_tags = get_all_pages(url, headers, {})
        release_tags = list(
            filter(
                lambda t: re.match(
                    r"release/.*/[0-9]+/.*/(edge|beta|candidate|stable)$", t["name"]
                ),
                all_rock_tags,
            )
        )

        for rtag in release_tags:
            # Get GH release (if any) for this tag
            url = f"{GIT_API_URL}/repos/{ORG}/{rock['name']}/releases/tags/{rtag['name']}"
            gh_release = requests.get(url, headers=headers)
            try:
                gh_release.raise_for_status()
            except requests.exceptions.HTTPError as err:
                if "404" in str(err):
                    # This is want we are looking for - a release tag without a GH release
                    pass
                else:
                    raise
            else:
                # There is already a GH release for this release tag...move on
                continue
            
            revision, track, risk = rtag["name"].split("/")[2:]
            new_release_tags.append(
                {
                    "full_name": f"{ORG}/{rock['name']}",
                    "name": rock["name"],
                    "sha": rtag["commit"]["sha"],
                    "tag": rtag["name"],
                    "revision": revision,
                    "track": track,
                    "risk": risk
                }
            )

    print(f"::set-output name=releases::{new_release_tags}")

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
SUPPORTED_RISKS = ["edge", "beta", "candidate", "stable"]

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
                    rf"release/.*/[0-9]+/.*/({'|'.join(SUPPORTED_RISKS)})$", t["name"]
                ),
                all_rock_tags,
            )
        )
        build_tags = list(
            filter(
                lambda t: re.match(
                    r"channels/.*/.*/.*/[0-9][0-9]\.[0-9][0-9]/[0-9]+$", t["name"]
                ),
                all_rock_tags,
            )
        )

        for rtag in release_tags:
            # Get GH release (if any) for this tag
            url = (
                f"{GIT_API_URL}/repos/{ORG}/{rock['name']}/releases/tags/{rtag['name']}"
            )
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

            rock_image_name, revision, track, risk = rtag["name"].split("/")[1:]

            logging.info(
                f"There is a release request tag {rtag['name']} without a GitHub release"
            )
            # Confirm that the corresponding release tag as an associated build tag
            corresponding_build_tag = [
                t
                for t in build_tags
                if t["name"].endswith(f"/{revision}") and f"{rock_image_name}/{track}" in t["name"] 
            ]
            if not corresponding_build_tag:
                logging.warning(
                    (
                        f"Release request tag {rtag['name']} does not have "
                        f"a matching build tag with revision number {revision}"
                    )
                )
                continue

            if corresponding_build_tag[0]["commit"]["sha"] != rtag["commit"]["sha"]:
                raise Exception(
                    f"The requested release tag {rtag['name']} does not point to the "
                    f"same commit as its corresponding build tag {corresponding_build_tag[0]['name']}"
                )

            build_tag_name = corresponding_build_tag[0]["name"]
            rock_name, rock_version, rock_base = build_tag_name.split("/")[-4:-1]
            revision, track, risk = rtag["name"].split("/")[2:]
            new_release_tags.append(
                {
                    "full_name": f"{ORG}/{rock['name']}",
                    "name": rock["name"],
                    "sha": rtag["commit"]["sha"],
                    "tag": rtag["name"],
                    "revision": revision,
                    "track": track,
                    "risk": risk,
                    "all_risks": f"{risk} {' '.join(SUPPORTED_RISKS[:SUPPORTED_RISKS.index(risk)])}",
                    "build_tag": build_tag_name,
                    "rock_name": rock_name,
                    "rock_version": rock_version,
                    "rock_base": rock_base,
                }
            )

    print(f"::set-output name=releases::{new_release_tags}")

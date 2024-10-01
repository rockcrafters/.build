#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from helper_functions import get_all_pages

ORG = "rockcrafters"
GIT_API_URL = "https://api.github.com"


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Validate the request for a new ROCK release"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="authz token for organization-wide read operations",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="ROCK project",
    )
    parser.add_argument(
        "--rock-name",
        required=True,
        help="ROCK name",
    )
    parser.add_argument(
        "--revision",
        required=True,
        help="ROCK revision",
    )
    parser.add_argument(
        "--risk",
        required=True,
        help="risk to release the ROCK to",
    )
    parser.add_argument(
        "--track",
        required=True,
        help="track to release the ROCK to",
    )
    args = parser.parse_args()

    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github+json",
    }

    # Find the ROCKs project and its contributors
    url = f"https://api.github.com/repos/{ORG}/{args.repo}/contributors"
    contributors = get_all_pages(url, headers, {})
    triggering_actor = os.getenv("GITHUB_TRIGGERING_ACTOR")

    contributors_logins = list(map(lambda c: c["login"], contributors))
    if triggering_actor not in contributors_logins:
        raise Exception(
            f"Release request made by {triggering_actor} for "
            f"{args.rock_name} on {args.repo}. "
            f"{triggering_actor} is NOT a contributor!"
        )

    # Get all tags
    url = f"{GIT_API_URL}/repos/{ORG}/{args.repo}/tags"
    all_rock_tags = get_all_pages(url, headers, {})
    tag_names = list(map(lambda t: t["name"], all_rock_tags))

    desired_release_request_tag = (
        f"release/{args.rock_name}/{args.revision}/{args.track}/{args.risk}"
    )
    # If release tag already exists, exit
    if desired_release_request_tag in tag_names:
        raise Exception(
            f"Requested release path {desired_release_request_tag} "
            f"already exists at {args.repo}."
        )

    # Does the build tag for the requested revision exist?
    build_tags = list(
        filter(
            lambda t: re.match(
                rf"channels/.*/{args.rock_name}/.*/[0-9][0-9]\.[0-9][0-9]/{args.revision}$",
                t,
            ),
            tag_names,
        )
    )

    if not build_tags:
        raise Exception(
            f"{triggering_actor} requested a ROCK release for {args.rock_name} "
            f"on {args.repo}. But the targeted revision {args.revision} "
            "has not yet been built (no channel tags with such revision number)."
        )

    print(f"::set-output name=rock-version::{build_tags[0].split('/')[-3]}")
    print(f"::set-output name=build-tag::{build_tags[0]}")

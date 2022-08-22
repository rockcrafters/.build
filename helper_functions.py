import argparse
import base64
import logging
import os
import requests
import yaml


def check_org_argparse(description) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--token",
        dest="token",
        required=True,
        help="authz token for organization-wide read operations",
    )
    parser.add_argument(
        "--workflow",
        dest="workflow",
        default=os.getenv("GITHUB_WORKFLOW"),
        help="workflow name under which this script is running",
    )
    parser.add_argument(
        "--on-repo",
        dest="on_repo",
        default=None,
        help="if provided, as <repo> (with the org name), it will only check that repository for updates",
    )

    return parser


def get_all_pages(url: str, headers: dict, params: dict) -> list:
    """Paginate over all the Git objects and return all"""
    params["per_page"] = 100
    page_num = 1

    objects = []
    while True:
        params["page"] = page_num
        page_objs = requests.get(url, headers=headers, params=params)
        page_objs.raise_for_status()
        objects += page_objs.json()

        if len(page_objs.json()) == 100:
            page_num += 1
        else:
            break

    return objects


def list_rocks_projects(api_url: str, org: str, headers: dict, single_repo: str = None):
    if single_repo:
        logging.info(f"Check for updates only on repo {single_repo}")
        exclude_repos = []
        # Get all the ROCK projects
        url = f"{api_url}/repos/{org}/{single_repo}"
        rocks_projects = [requests.get(url, headers=headers, params={}).json()]
    else:
        # Get which repos are to be excluded from this check
        url = f"{api_url}/repos/{org}/.github/contents/organization-workflows-settings.yml"
        org_workflow_settings = requests.get(url, headers=headers)
        org_workflow_settings.raise_for_status()
        org_workflow_settings_yaml = yaml.safe_load(
            base64.b64decode(org_workflow_settings.json()["content"]).decode()
        )

        exclude_repos = org_workflow_settings_yaml.get("exclude", {}).get(
            "repositories", []
        )

        if exclude_repos:
            logging.info(
                f"Excluding the following repositories from this check: {exclude_repos}"
            )

        # Get all the ROCK projects
        url = f"{api_url}/orgs/{org}/repos"
        params = {
            "type": "all",
            "sort": "updated",
            "direction": "asc",
        }
        rocks_projects = get_all_pages(url, headers, params)

    return rocks_projects, exclude_repos

#!/usr/bin/env python3

import argparse
import base64
import logging
import os
import requests
import sys
import yaml

ORG = "ubuntu-rocks"
GIT_API_URL = "https://api.github.com"


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

 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser(description="Scan the ubuntu-rocks GitHub organization, finding which ROCK repos have been updated and need a new build.")
    parser.add_argument("--token", dest="token", required=True,
                        help="authz token for organization-wide read operations")
    parser.add_argument("--workflow", dest="workflow", default=os.getenv("GITHUB_WORKFLOW"),
                        help="workflow name under which this script is running")
    args = parser.parse_args()

    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github+json"
        }
    
    # Get which repos are to be excluded from this check
    url = f"{GIT_API_URL}/repos/{ORG}/.github/contents/organization-workflows-settings.yml"
    org_workflow_settings = requests.get(url, headers=headers)
    org_workflow_settings.raise_for_status()
    org_workflow_settings_yaml = yaml.safe_load(base64.b64decode(org_workflow_settings.json()["content"]).decode())
    
    exclude_repos = org_workflow_settings_yaml.get("exclude", {}).get("repositories", [])
    
    if exclude_repos:
        logging.info(f"Excluding the following repositories from this check: {exclude_repos}")
    
    # Get all the ROCK projects
    url = f"{GIT_API_URL}/orgs/{ORG}/repos"
    params = {
        "type": "all",
        "sort": "updated",
        "direction": "asc",
    }
    rocks_projects = get_all_pages(url, headers, params)
    
    new_commits = []
    for rock in rocks_projects:
        if rock["name"] in exclude_repos:
            continue

        logging.info(f"Scanning channel branches in {rock['name']} project...")        
        # Get all channel branches
        url = f"{GIT_API_URL}/repos/{ORG}/{rock['name']}/git/matching-refs/heads/channels/"
        rock_branches = get_all_pages(url, headers, {})
        
        # Git API does not allow searching tags by commit
        url = f"{GIT_API_URL}/repos/{ORG}/{rock['name']}/tags"
        all_rock_tags = get_all_pages(url, headers, {})
        
        for channel in rock_branches:
            if channel["object"]["type"] != "commit":
                continue
            channel["name"] = channel["ref"].lstrip("refs/heads")
            
            sha = channel["object"]["sha"]
            
            logging.info(f"Latest commit for {rock['name']} on {channel['name']} is {sha}")
            # Need to find if any of the existing tags
            # for this channel, are for this commit.
            # Expected format: channels/x.y/...
            channel_track = "/".join(channel["name"].split("/")[:2])
            channel_tags = [t for t in all_rock_tags if t["name"].startswith(channel_track)]
            
            tags_for_commit = [ct for ct in channel_tags if ct["commit"]["sha"] == sha]
            
            if not tags_for_commit:
                # If tags_for_commit is empty,
                # then this current SHA has not yet been built,
                # otherwise, this SHA was already built in this 
                # branch, so the only thing that can still happen
                # is a tag promotion, which is a different process
                 
                new_commits.append({
                    "full_name": f"{ORG}/{rock['name']}",
                    "name": rock["name"],
                    "sha": sha,
                    "branch": channel["name"]
                })
      
    # NOTE: to avoid spawning too many workflow runs
    # and incentivate users to be more disciplined about
    # their commit/merge practices, we implement a 
    # business logic here of "batch builds". 
    # This means that if there's already a worklow run
    # ongoing in this repo, then all the new ROCK commits 
    # will have to wait (on queue) for the next batch build. 
    
    # TODO: a possible improvement to this business logic would 
    # be to evaluate on a per-ROCK basis, i.e., if there 
    # is already a workflow run, building a ROCK for a certain
    # ROCK project, then that ROCK project will have to wait
    url = f"{GIT_API_URL}/repos/{os.getenv('GITHUB_REPOSITORY', f'{ORG}/.build')}/actions/runs"
    params = {
        "branch": "main",
        "status": "in_progress",
        "exclude_pull_requestsboolean": "True",
        "per_page": "100"
    }
    # It is very unlikely to get > 100 workflows running in parallel
    workflows_running = requests.get(url, headers=headers, params=params).json()
    instances_of_this_workflow = [wf for wf in workflows_running["workflow_runs"] if wf["name"] == args.workflow]
    
    # If instances_of_this_workflow has more than one workflow
    # running, then there is already another instance of 
    # this workflow (self) already building something.
    # If this is the case, all the new commits go into 
    # queue, awaiting for the next run of this workflow.
    output_variable = "triggers"
    if len(instances_of_this_workflow) >= 2:
        output_variable = "queue"

    print(f"::set-output name={output_variable}::{new_commits}")

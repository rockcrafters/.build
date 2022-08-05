#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Infer the build 'risk' from a channel name."
    )
    parser.add_argument("--channel", dest="channel", required=True, help="channel name")
    args = parser.parse_args()

    branch = args.channel
    # expected format is channels/<track>/<risk>/<...>
    supported_risks = ["edge", "beta", "candidate", "stable"]
    try:
        risk = branch.split("/")[2]
    except IndexError:
        # this means a risk was not provided
        # default to "edge"
        risk = "edge"

    if risk in supported_risks:
        print(f"::set-output name=risk::{risk}")
    else:
        raise Exception(
            f"Inferred unsupported risk {risk} from branch name {branch}.\
        Supported risks are: {supported_risks}"
        )

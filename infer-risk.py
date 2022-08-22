#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Infer the build 'risk' from a channel name."
    )
    parser.add_argument("--channel", required=True, help="channel name")
    args = parser.parse_args()

    branch = args.channel.split("/")
    # expected format is channels/<track>/<risk>/<...>
    supported_risks = ["edge", "beta", "candidate", "stable", ""]
    
    track = branch[1]
    try:
        risk = branch[2]
    except IndexError:
        # this means a risk was not provided
        # default to "edge"
        risk = ""

    if risk in supported_risks:
        print(f"::set-output name=risk::{risk}")
        print(f"::set-output name=track::{track}")
    else:
        raise Exception(
            f"Inferred unsupported risk {risk} on track {track}, from branch name {args.channel}.\
        Supported risks are: {supported_risks}"
        )

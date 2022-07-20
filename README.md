# ROCKs' Builder: one CI/CD for all ROCKs

Building all the ROCKS from [ubuntu-rocks](https://github.com/ubuntu-rocks), in one place.

## Purpose

This is a built-in repository for hosting the CI/CD workflow responsible for 
building, testing and publishing ROCKs which are being hosted in the 
[ubuntu-rocks](https://github.com/ubuntu-rocks) organization.

Its purpose is tightly coupled with the organization's settings, meaning that 
the way the repository is structured, as well as its CI/CD workflows, are 
a byproduct of conventions, cross-repository dependencies and external tooling which 
have been put in place exclusively to be used within this GitHub organization 
and in compliance with this repository's expectations.

## Why?

The [ubuntu-rocks](https://github.com/ubuntu-rocks) organization is expected to 
host multiple repositories from which ROCKs should be built. Consider it as being 
a playground for learning how to design and build ROCKs without the burden of 
manually building, testing and publishing each ROCK, everytime there's a 
relevant update (be it a new feature commit, or an upstream security patch for a 
package the ROCK needs).

Therefore, this repository contains all the necessary hooks and workflows to 
automate the CI/CD for all ROCKs in the organization.

# How it works

## Developer's Guide

This repository needs to centrally manage and run CI/CD for multiple repositories 
across the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization. We could 
achieve a similar cross-repo CI/CD experience via [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows), [Starter Workflows](https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization), or even 
[Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action). 
The problem with these approaches however is that all of them rely on the ROCK repository to 
define the actual CI/CD workflows. This would break the concept of a standardized 
build, test and publishing process for all ROCKs, since each repository could 
easily influence the course of their workflows. Not to mention the use of sensitive 
CI/CD information, which would need to be made accessible for all repositories.

We want all CI/CD processes to be owned and enforced by Canonical, and 
executed at a central location, without compromising the transparent 
relationship between the CI/CD infrastructure and the ROCK repository 
(i.e. the ROCK repository and maintainers have a tight link and full visibility 
to the processes running within this central build repository)

The best way to enable such kind of centralized cross-repo management capabilities is through 
a GitHub App. 

### GitHub App requirements

What kind of GitHub App do we need for this repository to function as intended?

The GitHub App must:

 1. trigger a workflow in this build repository, whenever an event of interest takes place 
 anywhere in the organization
    1. an event of interest can be:
        - a new branch has been created in a repository
        - a new commit has been pushed to a branch of a repository
        - a new tag has been pushed in a repository
        - etc.

 2. allow to, via configuration, select repositories which are not to be watched (like this one)

### GitHub App configuration

Let's break down what needs to be done to enable and configure this GitHub App.

Please note that the following steps have already been performed in this organization, 
and are here listed for reproducibility purposes only.

**As an admin of [ubuntu-rocks](https://github.com/ubuntu-rocks)**, you need to:

 1. make sure the desired GitHub App exists
    - at the moment, we are using an existing [Probot](https://github.com/probot/probot) 
    app named [Organization Workflows](https://probot.github.io/apps/organization-workflows/). 
    - if it exists, and is public, it should be available via the [GitHub Marketplace](https://github.com/marketplace)
 2. from the [app page](https://github.com/apps/organization-workflows/), click configure
 3. select the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization
 4. select "All repositories" (we'll curate this list later on) and ensure the permissions are set to "*Read access to metadata*" and "*Read and write access to actions, administration, checks, code, and issues*"
 5. click install

#### Steps specific to the [Organization Workflows](https://probot.github.io/apps/organization-workflows/) GitHub App

First, we'll want to instruct the GitHub App about which repository will be receiving 
the workflow triggers, and which repositories are excluded from the app watchlist (as mentioned above in step 4.).

 1. make sure the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization as a [.github](https://github.com/ubuntu-rocks/.github) repository
 2. create a file named `organization-workflows-settings.yml` at the root of the 
 [.github](https://github.com/ubuntu-rocks/.github) repository, with the following content:

    ```yaml
    workflows_repository: .build

    include_workflows_repository: false
    exclude:
      repositories:
      - '.admin'
      - '.github'
      - 'rocks-pipelines'
    ```

    This is basically to say that: 
     - we want to trigger organization workflows in the [.build](https://github.com/ubuntu-rocks/.build) 
     repository (this one)
     - we want to exclude the [.build](https://github.com/ubuntu-rocks/.build) repository, 
     and a few others, from triggering the organization workflows 

#### The repository_dispatch workflow

The final step on the GitHub App configuration is to actually create the GitHub 
organization workflow which will receive the repository dispatch (trigger) from the 
App.

 1. in this [.build](https://github.com/ubuntu-rocks/.build) repository, create a 
 GitHub workflow file (under the `.github/workflows` folder - let's call it 
 `organization-workflow.yaml`), with the following content:

    ```yaml
    name: ROCKs Organization Workflow

    on:
      repository_dispatch:
        types: [org-workflow-bot]

    jobs:
    # JOBS: Jobs to be triggered here
    ```

    With the jobs being whatever the CI/CD should run, whenever there's an event
    of interest anywhere within [ubuntu-rocks](https://github.com/ubuntu-rocks) 
    (except in the excluded repositories from the previous section). See how it is
    currently in [this repository](https://github.com/ubuntu-rocks/.build/blob/main/.github/workflows/organization-workflow.yaml).
   
NOTE: it is this workflow's responsibility to make sure the original ROCK's commit is "[checked](https://docs.github.com/en/rest/checks/runs)".
By checking each run, we allow all ROCKs' commits to be traceable to their corresponding build. 
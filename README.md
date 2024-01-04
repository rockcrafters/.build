[![Trigger new builds for updated ROCKS](https://github.com/ubuntu-rocks/.build/actions/workflows/trigger-rock-build-on-changes.yml/badge.svg?branch=main)](https://github.com/ubuntu-rocks/.build/actions/workflows/trigger-rock-build-on-changes.yml)

---

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
achieve a similar cross-repo CI/CD experience via ROCK-specific [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows), [Starter Workflows](https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization), or even 
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

Any GitHub App would work! The reality is that the most important thing we need from the App, is **the token**! Many GitHub features and API operations (like Checks and Annotated tags) are only available for Apps, so what we need is the App token, with which we are authorized to perform such operations.

*Optionally*, the GitHub App could also be configured to monitor the entire organization, and upon certain events, trigger a `repository_dispatch` workflow in this repository. This way, the ROCKs would build as soon as there are commits being pushed to any ROCK repository throughout the organization...but this is a CI/CD improvement rather than a requirement. There are existing GitHub Apps that function in a similar way, and that we could use (like the existing [Probot](https://github.com/probot/probot)
app named [Organization Workflows](https://probot.github.io/apps/organization-workflows/), which is not currently being used in this organization due to reliability and security concerns)

### GitHub App configuration

Let's break down what needs to be done to enable and configure this GitHub App.

Please note that the following steps have already been performed in this organization, 
and are here listed for reproducibility purposes only.

Since we only need an App token, all we have to do is to create a mock "GitHub ROCKs App". **As an admin of [ubuntu-rocks](https://github.com/ubuntu-rocks)**, you need to:

 1. from the [ubuntu-rocks App settings](https://github.com/organizations/ubuntu-rocks/settings/apps), create a new GitHub App
 2. fill in the App's details, making sure that 
     - "Webhook" is only enabled if there's an actual application running somewhere, behind a webhook, and
     - at least the following permissions are granted:
       - Repository:
         - **Actions:** r/w
         - **Administration:** r
         - **Checks:** r/w
         - **Commit statuses:** r/w
         - **Contents:** r/w
         - **Environments:** r
         - **Issues:** r/w
         - **Metadata:** r
         - **Webhooks:** r
         - **Workflows:** r
       - Organization:
         - **Administration:** r
         - **Events:** r
         - **Members:** r
         - **Secrets:** r
       - User:
         - **Email addresses:** r
 3. click "Create GitHub App", **only on this account** (i.e. the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization)
 4. from the newly created App page, click on "Generate private key" (this will download a PEM file), and also copy the "App ID" number
 5. from the GitHub App's settings page, install the App into the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization, for all repositories
 6. go to [this repo's settings](https://github.com/ubuntu-rocks/.build/settings) and navigate to Secrets -> Actions
 7. create a "New repository secret" called **APP_ID** and paste the App ID number copied above
 8. create a "New repository secret" called **APP_PEM** and paste the *base64 encoded* contents of the PEM file downloaded above (i.e. `cat rocks-token-app.\<date\>.private-key.pem | base64 -w 0 && echo`). Afterwards, you can either securely keep this PEM file or delete it, because we can always generate a new private key for this App if need be
 9. these repository variables are then used from within the GitHub workflows, everytime we need to capture the GitHub App token. The retrieval of said token can be done via this GitHub action: <https://github.com/machine-learning-apps/actions-app-token>

### Additional configurations

There are repositories within the organization that we don't want to scan or build for, since they might be dedicated to something else than a ROCK (e.g. `.github` and `.build` repositories).

To create these exclusion rules, let's create a control file in the [organization's `.github` repository](https://github.com/ubuntu-rocks/.github/), called `organization-workflows-settings.yml` (note: this is the same file and syntax that one would use when working with the [Organization Workflows](https://probot.github.io/apps/organization-workflows/) GitHub App)

 1. make sure the [ubuntu-rocks](https://github.com/ubuntu-rocks) organization has a [.github](https://github.com/ubuntu-rocks/.github) repository
 2. create a file named `organization-workflows-settings.yml` at the root of the 
 [.github](https://github.com/ubuntu-rocks/.github) repository, with the following content:

    ```yaml
    workflows_repository: .build

    include_workflows_repository: false
    exclude:
      repositories:
      - '.admin'
      - '.github'
      - 'mock-rock'
      - '.build'
    ```

And that's it...the organization CI/CD workflows will not try to build any ROCKs for those repositories.

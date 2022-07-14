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

## How?

The aforementioned description can be a bit vague for those trying to fully 
understand what goes on within this repository.

For a more comprehensive understanding, please read the Developer's Guide and Usage in the [project's Wiki](https://github.com/ubuntu-rocks/.build/wiki/). These two sections 
provide the necessary information for core developers to contribute to this repository, 
and for Rockstars to understand how to plug their ROCK repositories to this build system.

NOTE: you can clone just the Wiki pages by running `git clone https://github.com/ubuntu-rocks/.build/wiki/`



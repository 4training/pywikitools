# Switch to Markdown for documentation

## Context and Problem Statement

When I started the repository, I used ReStructuredText for the documentation. It seemed better to me at the time because it was more powerful and more the Python standard. In the meantime, however, I realized using Markdown would have several benefits:

* more intuitive and much better known
* We also want to attract people for occasional contributions and most people (except deep Python nerds) are not familiar with RST syntax. The RST syntax is sometimes rather confusing
* We probably won't need the advanced features of RST at all
* The project will stay on github which is also clearly in favor of Markdown (in issue formatting etc.)
* The other 4training repositories (e.g. the [Flutter repository for the app](https://github.com/4training/app4training)) use markdown

## Considered Options

* Stay with ReStructuredText (RST)
* Migrate to Markdown

## Decision Outcome
Abandon RST and switch to Markdown

* There is no real disadvantages from that choice (see reasons above)
* The migration itself was also not that much work

Implemented with #102 / PR #108


# Use Markdown Architectural Decision Records

## Context and Problem Statement

We want to have good documentation, also on important decisions that are made during development. How to do that practically?

## Considered Options

* Don't worry about it – The information may be be found in some issues or by looking through the git log or by asking the developer
* Start using architectural decision records (ADR), specifically
  * [MADR](https://adr.github.io/madr/) 4.0.0 – The Markdown Architectural Decision Records
  * [adr-tools](https://github.com/npryce/adr-tools) with [Michael Nygard's template](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions) – The first incarnation of the term "ADR"

## Decision Outcome
Chosen option: "MADR 4.0.0", because

* It's good to document design decisions and to do that in a consistent way. MADR allows for structured capturing of any decision, is lean and is an active project
* adr-tools brings a command-line tool which I think is not necessary: we don't have to do and document architecture decision often and we would need to worry about how to install the tool etc
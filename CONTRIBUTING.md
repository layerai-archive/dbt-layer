# Contributing to Layer dbt Adapter

Whether you are an experienced open source developer or a first-time contributor, we welcome your contributions to the code and the documentation. Thank you for being part of our community!

### Table Of Contents

[Code of Conduct](#code-of-conduct)

[How can I contribute?](#how-can-i-contribute)
* [Reporting bugs](#reporting-bugs)
* [Suggesting enhancements](#suggesting-enhancements)
* [Contributing code](#contributing-code)

[How do I contribute code?](#how-do-i-contribute-code)
* [Setting up your environment](#setting-up-your-environment)
* [Running in development](#running-in-development)
* [Testing your changes](#testing-your-changes)
* [Submitting a pull request](#submitting-a-pull-request)

## Code of Conduct

This project and everyone participating in it is governed by the [Layer Code of Conduct](https://github.com/layerai/.github/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [community@layer.ai](mailto:community@layer.ai).

## How can I contribute?

### Reporting bugs

This section guides you through submitting a bug report for Layer. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior and find related reports.

Before creating bug reports, please check [this list](#before-submitting-a-bug-report) as you might find out that you don't need to create one. When you are creating a bug report, please [include as many details as possible](#how-do-i-submit-a-good-bug-report). Fill out [the required template](https://github.com/layerai/.github/blob/master/.github/ISSUE_TEMPLATE/bug_report.md), the information it asks for helps us resolve issues faster.

> **Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one.

#### Before Submitting A Bug Report

* **Check our [discourse](https://discourse.layer.ai/)** for a list of common questions and problems.
* **Perform a [cursory search](https://github.com/search?q=+is%3Aissue+user%3Alayerai)** to see if the problem has already been reported. If it has **and the issue is still open**, add a comment to the existing issue instead of opening a new one.

#### How Do I Submit A (Good) Bug Report?

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/). Create an issue on the relevant repository and fill in [the template](https://github.com/layerai/.github/blob/master/.github/ISSUE_TEMPLATE/bug_report.md).

Explain the problem and include additional details to help maintainers reproduce the problem:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples. If you're providing snippets in the issue, use [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem. You can use [this tool](https://www.cockos.com/licecap/) to record GIFs on macOS and Windows, and [this tool](https://github.com/colinkeenan/silentcast) or [this tool](https://github.com/GNOME/byzanz) on Linux.
* **If the problem wasn't triggered by a specific action**, describe what you were doing before the problem happened and share more information using the guidelines below.

Provide more context by answering these questions:

* **Did the problem start happening recently** (e.g. after updating to a new version of Layer) or was this always a problem?
* If the problem started happening recently, **can you reproduce the problem in an older version of Layer?** What's the most recent version in which the problem doesn't happen? You can install older versions of Layer with `pip install layer==<version>`.
* **Can you reliably reproduce the issue?** If not, provide details about how often the problem happens and under which conditions it normally happens.

Include details about your configuration and environment:

* **Which version of Layer are you using?** You can get the exact version by running `pip show layer` in your terminal.
* **What's the name and version of the OS you're using**?


### Suggesting enhancements

This section guides you through submitting an enhancement suggestion for Layer, including completely new features and minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand your suggestion and find related suggestions.

Before creating enhancement suggestions, please check [this list](#before-submitting-an-enhancement-suggestion) as you might find out that you don't need to create one. When you are creating an enhancement suggestion, please [include as many details as possible](#how-do-i-submit-a-good-enhancement-suggestion). Fill in [the template](https://github.com/layerai/.github/blob/master/.github/ISSUE_TEMPLATE/feature_request.md), including the steps that you imagine you would take if the feature you're requesting existed.

#### Before Submitting An Enhancement Suggestion

* **Perform a [cursory search](https://github.com/search?q=+is%3Aissue+user%3Alayerai)** to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.

#### How Do I Submit A (Good) Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://guides.github.com/features/issues/). Create an issue on the relevant repository and fill in [the template](https://github.com/layerai/.github/blob/master/.github/ISSUE_TEMPLATE/feature_request.md).

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include copy/pasteable snippets which you use in those examples, as [Markdown code blocks](https://help.github.com/articles/markdown-basics/#multiple-lines).
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Include screenshots and animated GIFs** which help you demonstrate the steps or point out the part of Layer which the suggestion is related to. You can use [this tool](https://www.cockos.com/licecap/) to record GIFs on macOS and Windows, and [this tool](https://github.com/colinkeenan/silentcast) or [this tool](https://github.com/GNOME/byzanz) on Linux.
* **Explain why this enhancement would be useful** to most Layer users and isn't something that can or should be implemented separately.
* **List some other tools where this enhancement exists.**
* **Specify which version of Layer you're using.** You can get the exact version by running `pip show layer` in your terminal.
* **Specify the name and version of the OS you're using.**


### Contributing code

If you'd like to go beyond reporting bugs and feature requests, you can follow the steps in [How do I contribute code?](#how-do-i-contribute-code) to set up your local development environment and open a pull request yourself. Before you start writing code, we recommend you [search existing issues](https://github.com/search?q=+is%3Aissue+user%3Alayerai) to see if there is someone else already working the feature you'd like to add. If not, please create an issue and mention in the comments that you're planning to open a pull request yourself.

## How do I contribute code?

## Prerequisites
- `pyenv`
- `poetry`
- `make`

### Python setup
We recommend using `pyenv`

Please run `make create-environment` to setup the recommended python version.

If you are using an Apple M1 machine, we recommend using `conda` via [Miniforge3](https://github.com/conda-forge/miniforge/). After installing conda please run

```
# Create and activate conda environment
make create-environment
conda activate build/dbt-layer
```

After that you should be able to run the rest of the `make` targets as normal
## Makefile
We use `make` as our build system.

Targets:
```
install                        Install dependencies
test                           Run unit tests
e2e-test                       Run e2e tests
format                         Apply formatters
lint                           Run all linters
check                          Run test and lint
check-package-loads            Check that we can load the package without the dev dependencies
publish                        Publish to PyPi - should only run in CI
clean                          Resets development environment.
help                           Show this help message.
create-environment             Set up virtual environment
delete-environment             Delete the virtual environment
```

## Dependency management
The `poetry` documentation about dependency management is [here](https://python-poetry.org/docs/dependency-specification/)

Every time you change dependencies, you should expect a corresponding change to `poetry.lock`. If you use `poetry` directly, it will be done automatically for you. If you manually edit `pyproject.toml`, you need to run `poetry lock` after

### A few tips:
#### How to add a new dependency
```
    poetry add foo
    # or
    poetry add foo=="1.2.3"
```

#### How to add a new dev dependency
```
    poetry add foo --dev
    # or
    poetry add foo=="1.2.3" --dev
```

#### How to get an environment with this package and all dependencies
```
    poetry shell
```

#### How to run something inside the poetry environment
```
    poetry run <...>
```

#### How to update a dependency
```
    poetry update foo
```

## Credits

Thanks for the [Atom](https://github.com/atom/atom) team for their fantastic open source guidelines which we've adopted in our own guidelines.

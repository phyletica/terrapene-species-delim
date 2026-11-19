# Overview

This is an
[open-science project](http://en.wikipedia.org/wiki/Open_notebook_science)
by the
[Phyletica Lab](http://phyletica.org)
to test hypotheses about box turtle species limits using phylogenetic
methods.

# Setting up the project's environment

To initialize the project's pixi workspace and install other software
dependencies, run the `setup_project_env.sh` script:

    bash setup_project_env.sh

# Test analyses with Gecko data

Before analyzing the *Terrapene* data, we wanted to verify that we had BEAST2
and the SPEEDEMON package working correctly.
To do this, we re-analyzed the *Hemidactylus* gecko data of
[Leaché et al. (2014)](https://doi.org/10.1093/sysbio/syu018)
that was analyzed by
[Douglas and Bouckaert](https://doi.org/10.1038/s42003-022-03723-z)
in their paper that introduced the SPEEDEMON method.

## Getting the gecko data

You can find the gecko data in the file `data/hemi.nex`.
These data were downloaded and converted to nexus format using the
`scripts/get_example_data.sh` Bash script.

## Setting up BEAST xml file

We used `bin/beauti` to setup the XML file for the BEAST2 SPEEDEMON analysis.

# Box turtle analyses

Our goal was to test the species delimitation hypotheses proposed by
[Martin et al. (2021)](https://doi.org/10.1111/1755-0998.13350)
by reanalyzing their data using SPEEDEMON.

# License

This work is marked <a href="https://creativecommons.org/publicdomain/zero/1.0/">CC0 1.0</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/zero.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">

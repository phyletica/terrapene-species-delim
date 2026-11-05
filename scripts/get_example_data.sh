#! /bin/bash

set -e

# Make sure we clean up and leave caller back from whence they called
current_dir="$(pwd)"
temp_dir="$(mktemp -d "/tmp/terra-sp-delim.XXXXXXXXXX")"
clean_up() {
    cd "$current_dir"
    rm -rf "$temp_dir"
}
trap clean_up EXIT

# Get path to directory of this script
script_dir="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
project_dir="$(dirname "$script_dir")"
pixi_toml_path="${project_dir}/pixi.toml"

data_dir="${project_dir}/data"
nex_path="${data_dir}/hemi.nex"

if [ -e "$nex_path" ]
then
    echo "Data file already exists: $nex_path"
    echo "If you really want to replace it, please delete it and rerun this script"
    exit 0
fi

if [ ! -e "$data_dir" ]
then
    mkdir "$data_dir"
fi

script_path="${project_dir}/scripts/beast2_integer_to_nexus.py"

snapper_tutorial_zip="snapper-delimitation-tutorial-2021.zip"
snapper_tutorial_url="https://github.com/BEAST2-Dev/beast-docs/releases/download/v1.0/${snapper_tutorial_zip}"
snapper_tutorial_path="${temp_dir}/${snapper_tutorial_zip}"

echo "Downloading SNAPPER tutorial zip to temp dir ..."
curl -L -o "$snapper_tutorial_path" "$snapper_tutorial_url"
echo "Extracting example XML file from tutorial zip ..."
unzip -j "$snapper_tutorial_path" "xml/RunA.xml" -d "$temp_dir"
echo "Converting data from XML to nexus format ..."
pixi run --manifest-path "$pixi_toml_path" python "$script_path" "${temp_dir}/RunA.xml" > "$nex_path"
echo "Nexus-formatted data written to $nex_path"

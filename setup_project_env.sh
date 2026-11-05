#! /bin/bash

set -e

# Make sure we leave caller back from whence they called
current_dir="$(pwd)"
clean_up() {
    cd "$current_dir"
}
trap clean_up EXIT

beast2_version="BEAST.v2.7.7"
beast2_archive="${beast2_version}.Linux.x86.tgz"
beast2_url="https://github.com/CompEvol/beast2/releases/download/v2.7.7/${beast2_archive}"
# Git commit SHA for the "v2.7" branch of speedemon
# speedemon_commit="1f56d1b"
beast2_packages=("speedemon" "snapper")
beast2_package_versions=("1.1.0" "1.1.5")


# Get path to directory of this script
project_dir="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pixi_toml_path="${project_dir}/pixi.toml"

echo "Running pixi install ..."
pixi install --manifest-path "$pixi_toml_path" 

dep_dir="${project_dir}/dependencies"
bin_dir="${project_dir}/bin"
beast2_pacman_path="${bin_dir}/packagemanager"

if [ ! -e "$dep_dir" ]
then
    mkdir "$dep_dir"
fi
if [ ! -e "$bin_dir" ]
then
    mkdir "$bin_dir"
fi

beast2_archive_path="${dep_dir}/${beast2_archive}"
beast2_dir="${dep_dir}/beast"

beast2_package_dir="${project_dir}/.beast"
if [ ! -e "$beast2_package_dir" ]
then
    mkdir "$beast2_package_dir"
fi

# Load modules
echo "Loading modules..."
source "${project_dir}/modules-to-load.sh" >/dev/null 2>&1 || echo "    No modules loaded"

# Get BEAST2
if [ ! -e "$beast2_archive_path" ]
then
    echo "Downloading $beast2_version ..."
    curl -L -o "$beast2_archive_path" "$beast2_url"
else
    echo "BEAST archive found; skipping download: '$beast2_archive_path'"
fi

echo "Extracting $beast2_version ..."
tar xzf "$beast2_archive_path" -C "$(dirname "$beast2_dir")"

echo "Updating $beast2_version scripts with project package directory..."
for exe_path in "${beast2_dir}/bin"/*
do
    sed "s|\"\$JAVA\" |\"\$JAVA\" -Dbeast.user.package.dir=\"${beast2_package_dir}\" |g" "$exe_path" > "${exe_path}.tmp" && mv "${exe_path}.tmp" "$exe_path" && chmod +x "$exe_path"
done

for exe_path in "${beast2_dir}/bin"/*
do
    exe_name="$(basename "$exe_path")"
    if [ ! -e "${bin_dir}/${exe_name}" ]
    then
        echo "Symlinking $exe_name to ${bin_dir}/${exe_name} ..."
        ln -s "$exe_path" "${bin_dir}/${exe_name}"
    else
        echo "$exe_name symlink found; skipping symlinking ..."
    fi
done

for i in "${!beast2_packages[@]}"
do
    beast_package="${beast2_packages[i]}"
    beast_package_version="${beast2_package_versions[i]}"
    "$beast2_pacman_path" -add "$beast_package" -version "$beast_package_version" -dir "$beast2_package_dir"
done

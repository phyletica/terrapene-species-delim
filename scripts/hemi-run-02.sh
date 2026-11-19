#! /bin/bash

set -e

run=02
xml_prefix="hemi"

project_dir=".."
bin_dir="${project_dir}/bin"
data_dir="${project_dir}/data"
out_dir="${project_dir}/beast-output-${xml_prefix}"

if [ ! -e "$out_dir" ]
then
    mkdir "$out_dir"
fi

pixi_toml_path="${project_dir}/pixi.toml"

xml_path="${data_dir}/${xml_prefix}.xml"

out_prefix="${out_dir}/${xml_prefix}-run-${run}-"

pixi run --manifest-path "$pixi_toml_path" "${bin_dir}/beast" -seed "$run" -prefix "$out_prefix" "$xml_path"

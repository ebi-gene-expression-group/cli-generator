# cli-generator

This package aims to provide convenience scripts
to generate command line interface boilerplate
and Galaxy wrappers for Python and R libraries.

# Installation

Since this is in any phases, and will likely require
development input, the best might be to simply clone from github
and create a python virtual environment where dependencies are made available:

```
git clone https://github.com/ebi-gene-expression-group/cli-generator
cd ~/Develop/cli-generator
python -m venv venv-cg
source venv-cg/bin/activate
pip install PyYAML jinja2
```

After that, to use it, simply activate the environment

```
~/Develop/cli-generator
source venv-cg/bin/activate
```

and directly call the scripts on that directory (`python YAML2RScript` or `python YAML2GalaxyTool`).

# General process

Most of the Python codebase expects a YAML file
where the desired calls from a specific library
should be encoded. This YAML can be written manually
for the case of Python methods or automatically
for the case of R methods.

This tool aims to be of assistant for:
1.- Writing R code to a script that uses a set of calls from one or more libraries
2.- Writing a Galaxy wrapper to call CLIs like the generated in (1) or simply for any CLI.

In the case of writing a Galaxy wrapper (2), there are also other alternatives like [planemo](https://planemo.readthedocs.io/en/latest/writing.html).
If the command line call that you are trying to wrap is very simple and only uses a couple of positional arguments, you might be better
off with planemo. If your tool is complex and has many arguments, this tool might be useful.

# YAML structure

The first section of the YAML file that YAML2GalaxyTool and YAML2RScript tools will read are mostly related to Galaxy:

```
cli_call: 'seurat-plot.R'
galaxy_tool:
  id: seurat_plot
  name: Plot
  description: with Seurat
  profile: 18.01
  version: "@SEURAT_VERSION@"
  macros:
    - seurat_macros.xml
  macro_expands_header:
    - requirements
    - version
  macro_expands_footer:
    - citations
```

- cli_call: The main script call that galaxy needs to decorate with arguments. Usually the name of the script itself,
with some relative path if using an interpreter
- galaxy_tool: This section includes general header fields for the Galaxy wrapper to be written
    - id: The ID to use for the galaxy tool.
    - name: Human readable name of the Galaxy tool (visible directly in the UI)
    - description: The description used in Galaxy right after the tool name (visible in the UI)
    - profile: The Galaxy profile version for the tool.
    - version: The version for the Galaxy tool
    - macros: A list of files within the Galaxy wrapper directory with XML macros for the tool.
    - macro_expands_header: A list of macros, available in the `macros` files mentioned before, that will be expanded in the tool's header (that is, before the command section).
    - macro_expands_footer: A list of macros, available in the `macros` files mentioned before, that will be expanded in the tool's footer (that is, after the help and tests).

The following part, the commands, details the different commands and their options. These commands are meant to be library calls in R (in the future, in python as well), and
for the Galaxy wrapper, only the options of each call are relevant. The command part follows this structure:

```
commands:
  - call: 'load_seurat4_packages_for_format'
    dependencies:
      - workflowscriptscommon
      - optparse
    options:
      - long: formats
        type: internal
        value: 'c(opt$query_format, opt$anchors_format, opt$reference_format)'
  - call: 'read_seurat4_object'
    dependencies:
      - scater
      - SeuratDisk
    options:
      - long: input-object-file
        short: i
        type: file_in
        call_alias: input_path
        human_readable: 'Input file'
        help: "Query file with Seurat object in either RDS-Seurat, Loom or SCE"
      - long: input-format
        type: string
        call_alias: format
        human_readable: 'Input format'
        default: 'seurat'
        help: 'Either loom, seurat, anndata or singlecellexperiment for the input format to read.'
    output:
      - var_name: seurat_object
```

The commands section can have as many library calls as desired (in this case, `load_seurat4_packages_for_format` and `read_seurat4_object` are library calls, in this case
from workflowscriptscommon). Each call can have defined `dependencies`, `options` and `output`. The most important are probably the last two. The options will be a list
of potential arguments that the call that they are within will receive. For instance, `read_seurat4_object` receives in R two arguments or options: `input-object-file` and
`input-format`. An option will have the following fields:

- long: The long name of the option, required. This is normally what in a command line utility would be called with the double dash (--), for instance
`input-object-file` in this case: `seurat-plot.R --input-object-file <my-file>`. Required.
- short: A short alias for the same option. In the case of the `input-object-file` this could be `i`, to be used as `-i` by the command line program. Optional.
- type: Either one of `string`, `integer`, `float`, `list`, `list_numeric`, `string_or_file`, `boolean`, `file_in`, `file_out` and `internal`.
Internal is only relevant for R code and is used to pass the output of a previous call into the current one. Required.
- call_alias: This mostly relevant in R code only, and it is needed when the argument for the library call is not the same as what we want to expose in the command line. In the above example
it would mean that in the command line the script expects `--input-format` but then to the library call the value captured here will be passed to the `format` option. Optional.
- human_readable: This will be the name used for the variable in the UI (to be shown to the user). This is optional, in general, if not available, the `long` field will be capitalized
and any underscores changed to spaces.
- default: A default value for the option.
- help: Long text describing the option, used as help in Galaxy. Optional.
- options: A list of either strings or `key: value` pairs with potential values (and their explanation) for the argument. If this is available, it will mean that the option
will be presented in Galaxy as a drop down selection, with the options listed here. Optional. If used, the `default` has to be set.

Finally, the output of each call, can be one or more entities coded as `var-name`. These are neglected for the Galaxt wrapper, but are relevant when writing automated R code. The output of
one call can be passed to another call as an `internal` option, specifying the var_name.



## YAML generation from R methods documentation (Rd files)

Given a set of functions that are desired for a specific
R package:

- Start a conda or equivalent environment where 
  the R executable has installed the R library for which
  we want to generate code. For this example with Seurat R package
  and a previously generated Seurat conda environment:
  
```
conda activate seurat
Rscript Rd2YAML.R Seurat
```
  
This will list all potential Rd files. From those, pick the desired one
and run (using in this example `RunTSNE.Rd`):

```
Rscript Rd2YAML.R Seurat RunTSNE.Rd
[1] "Calls available for Rds and package selected:"
[1] "RunTSNE matrix"
[1] "RunTSNE DimReduc"
[1] "RunTSNE dist"
[1] "RunTSNE Seurat"
[1] "...use one of the above first tokens as the next argument."
```

Finally, choose one of the methods from the first 
column and use it as the next argument, providing 
an output path as a last argument.

```
Rscript Rd2YAML.R Seurat RunTSNE.Rd RunTSNE my-tsne-trial.yaml
```

## R code from YAML

To generate a YAML of a function you will want to concatenate YAML files from different R functions, for instance
for running UMAP you will at least need to load data, run UMAP and then write out the object and possibly the embeddings
file. In this case for instance, the YAML would look like:

```
commands:
  - call: 'read_seurat4_object'
    dependencies: workflowscriptcommons
    options_aliases:
      - option: input-format
        call: format
    options:
      - long: input-path
        short: i
        type: file_in
        human_readable: 'Input file'
        help: "Input file with Seurat object in either RDS-Seurat, Loom or SCE"
      - long: input-format
        type: string
        human_readable: 'Input format'
        default: 'seurat'
        help: 'Either loom, seurat, anndata or singlecellexperiment for the input format to read.'
    output:
      - var_name: seurat_object
  # all of UMAP below is written by the previous part, but we modify from there the options that should receive internals.
  - call: RunUMAP
    dependencies: Seurat
    options:
    - long: object
      default: ''
      type: internal
      var_name: seurat_object
    ...UMAP options written by previous call...
    output:
      - var_name: seurat_object_umap
  - call: 'write_seurat4_object'
    parsing_opts:
      - r_sep: "_"
    options_aliases:
      - option: output-format
        call: format
    options:
      - long: seurat_object
        type: internal
        var_name: seurat_object_umap
      - long: output-path
        type: file_out
      - long: output-format
        type: string
        default: seurat
```

Note how the output fields are connected to the following command's options type 'internal'. You want to check as well
that all options have a valid type and that help fields don't have conflicting quotes and double quotes, then run using the curated YAML file:


```
# source cli-generator pip environment
python YAML2RScript.py -i curated_YAML.yaml -o path/to/resulting/my-script.R
```

## Galaxy code from YAML

Using the same YAML, you can attempt a first Galaxy wrapper by calling:

```
python YAML2GalaxyTool -i curated_YAML.yaml -o GalaxyTool.xml
```

Normally one would either work from this GalaxyTool XML file to improve, adding tests and documentation among others.

Then the usual thing to do would be to lint it and test it with planemo.

# Macro mapping

Some Galaxy tools might need to replace sets of command lines and declaration parts
for groups of options. For instance, a set of options that define the input might
have their logic for declaration and/or commands be part of macros, as they will be used
for many tools.

We define a YAML structure to codify such association between groups of options and macros.
This YAML contains an array, where each element contains the tuple `(option_group, pre_command_macros, post_command_macros,
input_declarations, output_declarations)`. For instance:

```
---
- option_group:
    - input-object-file
    - input-format
  pre_command_macros:
    - INPUT_OBJ_PREAMBLE
  post_command_macros:
    - INPUT_OBJECT
  input_declaration_macros:
    - input_object_params
- option_group:
    - output-object-file
    - output-format
  post_command_macros:
    - OUTPUT_OBJECT
  output_declaration_macros:
    - output_object_params
```

This means that if on our set of options, we have options with long `input-object-file` AND `input-format`,
then these two options won't be treated directly by the option/section writer, but instead
they will be skipped and the `pre_command_macros`, `post_command_macros` and `input_declaration_macros`
will be written instead. And then we call:

```
python YAML2GalaxyTool -i curated_YAML.yaml -o GalaxyTool.xml -m macro_mapper.yaml
```

# Advanced options for Galaxy

A subset of options can be grouped for Galaxy purposes under "Advanced options". For this,
add the "advanced: True" property on each option that should fall under this category.

```
    options:
      - long: seurat_object
        type: internal
        var_name: seurat_object_umap
      - long: output-path
        type: file_out
      - long: output-format
        type: string
        advanced: True
        default: seurat
```





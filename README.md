# cli-generator

This package aims to provide convenience scripts
to generate command line interface boilerplate
and Galaxy wrappers for Python and R libraries.

# General process

Most of the Python codebase expects a YAML file
where the desired calls from a specific library
should be encoded. This YAML can be written manually
for the case of Python methods or automatically
for the case of R methods.

# YAML structure



## YAML generation for R methods

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




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
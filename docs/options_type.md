# Options classes

For all parameter classes, the following fields are expected and required:

- long: the long argument name, which you should normally make to match to library call
argument that you are trying to expose. If the argument should be used as `--my-argument`
then the long value should be `my-argument`. The Option classes for each implementation should
transform part of this if needed, for instance, many R library calls would expect `my.argument`
instead of `my-argument`.

The cli-generator accepts the following classes of options:

## Input file (`file_in`)

A typical file input option, which should allow the underlying cli to have all the logic
to:

- Fail if the file is not optional.
- Check that the file exists or error out.
- Provide any pre-processing of the file needed (which needs to be specified separately)
- Feed in the variable holding the file to the library call being wrapped.

## Output file (`file_out`)

An output file, which essentially means:

- Handling the part of the output of the library call that needs to be left in the file.
- Making sure the file gets written to the output path specified.

## String (`string`)

The simplest of all parameters, simply pass along.

## List (`list`)

Like a string parameter, but involves a step of breaking up the elements by a separator and providing
the library method with a list or vector, possibly typed to a particular type (int, double, etc)

## Boolean (`boolean`)



## Integer

##

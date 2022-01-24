library('readr')
library('rlang')
library('lobstr')

recursive.tree <- function(call, name) {
  for (i in 0:lenght(call)) {
    if (is_symbol(call[[i]])) {
      print(call[[i]])
      print(typeof(as_string(call[[i]])))
      print(typeof(name))
      if (as_string(call[[i]]) == name) {
        return(call)
      }
    }else if (is_call(call[[i]])) {
      recursive.tree(call_args(call[[i]]), name)
    }
  }
}

args = commandArgs(trailingOnly = TRUE)
R_file = read_file(file = args[1]);
name = read_file(file = args[1]);
R_file_exp = parse_exprs(R_file);


h <- recursive.tree(R_file_exp, 'verbose')
print(h)


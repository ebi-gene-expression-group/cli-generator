library('readr')
library('rlang')
library('lobstr')

args = commandArgs(trailingOnly = TRUE)
R_file = read_file(file=args[1]);
name = read_file(file=args[1]);
R_file_exp =  parse_exprs(R_file);
good_call <- ''
condition2 <- TRUE
recursive.tree <- function(call, name) {
                condition = 0
                print("yo")
                while (condition < length(call)&&condition2 == TRUE){
                        condition=condition+1
                        print("ya")
                        if (is_symbol(call[[condition]])){
                                print(call[[condition]])
                                print(typeof(as_string(call[[condition]])))
                                print(typeof(name))

                                if (as_string(call[[condition]])==name){
                                        good_call <-  call
                                        condition2 <- FALSE
                                }

                        }else if(is_call(call[[condition]])){
                                recursive.tree(call_args(call[[condition]]), name)
                        }

                }
        return (good_call)
        }

h <- recursive.tree(R_file_exp, 'verbose')
print(h)


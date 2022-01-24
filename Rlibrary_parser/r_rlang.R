library('readr')
library('rlang')
library('pracma')

################# PRE TREATMENT##################################

#Get the file wanted for parsing, by taking the cli arguments here
args = commandArgs(trailingOnly = TRUE)
R_file = read_file(file=args[1]);
look_to = args[2];
new_arg = parse_exprs(args[3])
#Transform txt into R expression
R_file_exp =  parse_exprs(R_file);
good_call <- 'call not found'
condition2 <- TRUE

#########################FUNCTIONS#####################################

#'Function to create the tree of calls in a R script and returns infos about the call wanted
#' @param call a piece of R scripcontaining the R function we want to extract infos from MUST BE A R EXPRESSION
#' @param name the nameof the function we want to wrapp and get infos from (char)
#' @return good_call a rlang call object that contain all the param names and default values that are intersting for wrapping
#' @example
#'
#' recursive.tree(" function1 <- function(param1 = blabla, param2 = bloblo) { ... } \n function2 <- function(param1 = blibli, param2 = bleble) {...}" , "function1")
#' this will return good_call containing :
#' function(param1 = blabla, param2 = bloblo) { ... }
#'
recursive.tree <- function(call, name) {
                condition = 0
                #while we do not navigate through every call and while we do not found a call named like the function we are looking for we keep going
                while (condition < length(call)&&condition2 == TRUE){
                        condition=condition+1
                        #if we have a : a <- b scheme
                        if (is_symbol(call[[condition]])){
                                #if one of the element of ["a","<-","b"] is equal to name
                                if (all(as_string(call[[condition]])==name)){
                                        condition2 <<- FALSE
                                        good_call <<- call
                                }
                        }else if(is_call(call[[condition]])){
                                #keep creating the tree
                                if(all(call_name(call[[condition]])==name)){
                                        condition2 <<- FALSE
                                        good_call <<- call[[condition]]
                                        }
                                recursive.tree(call_args(call[[condition]]), name)
                        }
                }
        #return good_call, the call that respond to these scheme : ["name","<-",good_call]
        return (good_call)
        }

#Function that create a matrix with all name , default values and type of the function we want to wrapp
info.matrix<- function(liste){
        matrice <- c('name','default','type')
        for(k in (1:length(liste))){
                type_ <- typeof(liste[[k]])
                default_ <- expr_label(liste[[k]])
                name_ <- names(liste[k])
                matrice <- rbind(matrice,c(name_,default_,type_))
                }
        return(matrice)
        }
#function that extract infos about the return call of the function we want to parse
treat.returncall <- function(returncall){
       print(call_args(returncall))
       returned <- sapply(call_args(returncall),expr_label)
       check_return <- call_name(returncall)
       if(all(check_return == 'return')){
        return(c(check_return,'',returned))
       }else{
        print('not a return call')
        }
    }

############################# SCRIPT ###########################

#launch the function recursive tree
to_modify <- recursive.tree(R_file_exp, look_to)
#get infos in the call founded
if(is_call(to_modify)){
        print("Function is called but not created here, impossible to found output")

       }else{
       function_core <- call_args(to_modify[[2]])
       function_core <- function_core[[2]]
       for(k in (1:length(call_args(function_core))+1)){
                if(is_call(function_core[[k]])){
                        if(all(call_name(function_core[[k]])=='return')){
                        function_output <<- function_core[[k]]}
                }
        }
        function_args <- call_args(to_modify[[2]])[[1]]
        lamatrice <- info.matrix(function_args)
        #function_output <- expr_label(function_output)
        function_output <- treat.returncall(function_output)
        lamatrice <- rbind(lamatrice, function_output)
        MASS::write.matrix(lamatrice,file='infos.csv', sep=';')

}






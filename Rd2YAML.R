#!/usr/bin/env Rscript

# Title     : TODO
# Objective : TODO
# Created by: pmoreno
# Created on: 10/05/2021

library(yaml)

options <- commandArgs(trailingOnly = TRUE)
if(length(options)<4) {
  print("Please provide 4 arguments in this order: ")
  print(" - package name, for example Seurat")
  print(" - Rd name, for instance ScaleData.Rd. For a package, Rd names can be found through `db <- tools::Rd_db(package)`")
  print(" - tool name, for instance ScaleData")
  print(" - YAML output file path")
}
package<-options[1] # Seurat
rdName<-options[2] # ScaleData.Rd
tool<-options[3] # ScaleData
yaml_output<-options[4] # output path

# Get db for tool
db <- tools::Rd_db(package)
# inspect with
# head(names(db))

# Pick a tool from the names:
Rd<-db[[rdName]]
tool_level<-package

get_usage_arguments<-function(Rd, tool, tool_level) {
  tags<-tools:::RdTags(Rd)
  # Locate the usage
  usage_index<-match("\\usage", tags)
  usage<-Rd[[usage_index]]

  # Get methods
  # Use desired method as argument, pick all RCODE tags that go after
  # remove blank lines and use this to come up with list of parameters
  # and expected types.
  method_indexes<-which(tools:::RdTags(usage) %in% "\\method")
  # pick the method index for the desired tool and level
  method_index=-1
  upper_bound=-1
  for(index in method_indexes) {
    if(tool %in% unlist(usage[[index]]) && tool_level %in% unlist(usage[[index]]) ) {
      method_index<-index
      if(index == max(method_indexes))
        # This is last method, so the upper bound is the length of the usage
        upper_bound<-length(usage)
        # this is picking more than it should
      else
        upper_bound<-method_indexes[(method_indexes %in% method_index)+1]
      break
    }
  }

  args_usage<-list()
  # Go through usage lines for the desired method
  au_count<-1
  for(i in method_index+1:upper_bound) {
    u_stripped<-gsub("[\r\n]", "", usage[i])
    if(startsWith(u_stripped, "(") || startsWith(u_stripped, ")") || length(u_stripped)==0)
      next
    if(tools:::RdTags(usage[i]) != "RCODE")
      next
    m<-regexec("([^,\\s]+),{0,1}(\\s*=\\s*([^,\\s]+)){0,1},{0,1}", u_stripped, perl=TRUE)
    # commas still on the default
    res<-regmatches(u_stripped, m)
    arg_usage<-list(long=res[[1]][2])
    if(length(res[[1]])==4) {
      arg_usage$default=res[[1]][4]
    }
    args_usage[[au_count]]<-arg_usage
    au_count<-au_count+1
  }

  # Identifiy types of arguments based on examples
  for(i in 1:length(args_usage)) {
    if(args_usage[[i]]$default == "NULL" || args_usage[[i]]$default == "NA")
      next
    if(!is.na(as.numeric(args_usage[[i]]$default))) {
      if(!is.na(as.integer(args_usage[[i]]$default))) {
        args_usage[[i]]$type<-"integer"
        args_usage[[i]]$default<-as.integer(args_usage[[i]]$default)
      }
      else {
        args_usage[[i]]$type<-"double"
        args_usage[[i]]$default<-as.double(args_usage[[i]]$default)
      }
    } else if(!is.na(as.logical(args_usage[[i]]$default))) {
      args_usage[[i]]$default<-as.logical(args_usage[[i]]$default)
      args_usage[[i]]$type<-"boolean"
    } else {
      args_usage[[i]]$default<-gsub("\"", "", args_usage[[i]]$default, fixed = T)
      args_usage[[i]]$type<-"string"
    }
  }
  return(args_usage)
}

get_arguments_arguments<-function(Rd, tool) {
  # Get tags in Rd
  tags<-tools:::RdTags(Rd)
  # Locate the arguments tag
  args_index<-match("\\arguments", tags)
  arguments<-Rd[[args_index]]

  # clean up empty lines from arguments by selecting only \item entries
  arguments[which(tools:::RdTags(arguments) %in% c("\\item"))]->arguments_clean

  args_list<-list()
  i<-1
  for(arg in arguments_clean) {
    arg_named_list<-list()
    merged_desc<-""
    for(desc in arg[2]) {
      merged_desc<-paste0(merged_desc, gsub("\n", "", desc), collapse=" ")
    }
    arg_named_list['long']<-unlist(arg[1])
    arg_named_list['help']<-merged_desc
    args_list[[i]]<-arg_named_list
    i<-i+1
  }
  return(args_list)
}

u_args<-get_usage_arguments(Rd, tool, tool_level)
a_args<-get_arguments_arguments(Rd, tool)

for(u in 1:length(u_args)) {
  for(a in 1:length(a_args)) {
    if(u_args[[u]]$long == a_args[[a]]$long) {
      u_args[[u]]$help<-a_args[[a]]$help
    }
  }
}

call<-list()
call$call<-tool
call$options<-u_args
call$output<-list()

write_yaml(call, yaml_output)



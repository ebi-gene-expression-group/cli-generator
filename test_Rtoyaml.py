import re
import subprocess
import yaml as yam
import os
from Rtoyaml import *

r_input = "test.R"
# r_input  = "monocle_format.R"

shebang_R = re.compile("[.]Rscript")
shebang_R1 = re.compile("R")

with open(r_input, 'r') as file:
    txt = file.read()
    list_files = txt.split("\n")
    deps = get_dependencies(txt)
    get_output(list_files)
    if shebang_R.search(list_files[0]) or shebang_R1.search(list_files[0]):
        names = get_all_function_r(txt)
        args = get_args_R(txt, names)
        dictio = fill_arg(args)
        print(names)
        print("helllo " + str(dictio))
        for fx_call in dictio:
            deps = get_dependencies(txt)
            for values in dictio[fx_call]:
                try:
                    classe = get_variable_class(dictio[fx_call][values]["default"])
                    dictio[fx_call][values]["type"] = classe
                except:
                    pass
                try:
                    documentation = get_doc(values, fx_call, dictio, txt)
                    dictio[fx_call][values]["help"] = documentation
                except:
                    pass
        command_dict = {}
        all_fonction = []
        for fx_call in dictio:
            to_append = {}
            to_append["call"] = fx_call
            to_append["dependencies"] = deps
            to_append["output"] = [{'var_name' : str(fx_call)}]
            arg_info = []
            for argument in dictio[fx_call]:
                arg_info.append(dictio[fx_call][argument])
            to_append["options"] = arg_info
            #to_append["options_aliases"] =
            #to_append["output"]
            all_fonction.append(to_append)
        command_dict["commands"] = all_fonction



        with open("yo.yaml", "w") as to_fill:
            yam.dump(command_dict, to_fill)

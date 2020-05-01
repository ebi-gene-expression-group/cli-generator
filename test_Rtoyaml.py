import re
import subprocess
import yaml as yam
import os
import Rtoyaml

#adresse  = "test.R"
adresse  = "monocle_format.R"
#############templates################################
shebang_R = re.compile("[.]Rscript")
shebang_R1 = re.compile("R")

###################Functions and class#######################""


with open(adresse) as file:
    txt = file.read()
    liste = txt.split("\n")
    dependencie = get_dependencies(txt)
    get_output(liste)
    if shebang_R.search(liste[0]) or shebang_R1.search(liste[0]):
        print("hiiiiii")
        names = get_all_function_r(txt)
        args = get_args_R(txt,names)
        dictio = fill_arg(args)
        print(names)
        print("helllo " + str(dictio))
        for fonction in dictio:
            dependencie = get_dependencies(txt)
            for values in dictio[fonction]:
                try:
                    classe = get_variable_class(dictio[fonction][values]["default"])
                    dictio[fonction][values]["type"] = classe
                except:
                    pass
                try:
                    documentation = get_doc(values, fonction, dictio, txt)
                    dictio[fonction][values]["help"] = documentation
                except:
                    pass
                print("DICTIOOOOOO \n \n \n")
        command_dict = {}
        all_fonction = []
        for fonction in dictio:
            to_append = {}
            to_append["call"] = fonction
            to_append["dependencies"] = dependencie
            to_append["output"] = [{'var_name' : str(fonction)}]
            arg_info = []
            for argument in dictio[fonction]:
                arg_info.append(dictio[fonction][argument])
            to_append["options"] = arg_info
            #to_append["options_aliases"] =
            #to_append["output"]
            all_fonction.append(to_append)
        command_dict["commands"] = all_fonction



        with open("yo.yaml", "w") as to_fill:
            yam.dump(command_dict, to_fill)

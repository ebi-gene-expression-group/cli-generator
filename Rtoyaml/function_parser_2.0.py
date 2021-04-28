import re
import subprocess
import yaml as yam
import os


def get_all_function_r(txt):
    """ get the name of the functions that match with function name declaration patern return all name under a list"""
    function_name = re.compile("\n([A-z]*) <- function[(]")
    names = function_name.findall(txt)
    return names

def get_args_R(txt,names):
    """ get arguments of a specific function return them under a list"""
    all_args = []
    for name in names:
        a = re.compile(name + " <- function[(]([^{}]*)[)]")
        args = a.findall(txt)
        args = args[0]
        args = args.replace(" ","")
        args = args.split(",")
        args.append(name)
        all_args.append(args)
        print(args)
    return(all_args)

def get_variable_class(variable):
    """take as input a variable=x string"""
    re_classe = re.compile("[^\"\n]+")
    try:
        a = subprocess.check_output("Rscript -e \"class(" + variable + ")\" ", shell=True)
        a = re_classe.findall(str(a))[1]
        if a == 'integer' or a == 'NULL':
            a = 'string'
    except:
        a = 'string'
    return a


def get_doc(variable, fonction, dictio, texte):
    """get the documentation specific to an argument of a function"""
    doc_patern = re.compile("@param ("+ str(variable) + " [^\n]*)" )
    documentation = doc_patern.findall(texte)
    count = 0
    for a in dictio:
        for b in dictio[a]:
            if variable in b:
                count += 1
            if a == fonction:
                return documentation[count-1]



def get_dependencies(texte):
    """get all the dependencies without function specification, output is a list"""
    depend_patern = re.compile("@importFrom ([A-z]+)")
    to_import = depend_patern.findall(texte)
    for element in to_import:
        if to_import.count(element) > 1:
            to_import.pop(to_import.index(element))

    #for element in to_import:
    #    a = subprocess.check_output("Rscript -e install.packages(" + str(element) + ") ", shell=True)
    #    if a != 0:
    #        to_import.pop(index(element))
    return to_import

def get_output(liste):
    """ WIP get the specific output of a function"""
    last = 0
    teste_fonction = re.compile("([A-z]*) <- function[(]")
    specific_dict = {}
    out_fonction = True
    stock_out_fonction = []
    for element in liste:
        if teste_fonction.match(element)  != None:
            print("yo")
            current_fonction = teste_fonction.findall(element)[0]
            specific_dict[current_fonction] = stock_out_fonction
            compte = 0
            last = liste.index(element)
            stock_out_fonction = []
            out_fonction = False
        if 'compte' in locals() and '{' in element and not out_fonction:
                compte +=1
        if 'compte' in locals() and '(' in element and not out_fonction:
                compte +=1
        if 'compte' in locals() and ')' in element and not out_fonction:
                compte -= 1
        if 'compte' in locals() and '}' in element and not out_fonction:
                compte -= 1
        if 'compte' in locals() and compte == 0 and not out_fonction:
            specific_dict[current_fonction] = specific_dict[current_fonction]+ liste[last:liste.index(element)]
            out_fonction = True
        if out_fonction:
            stock_out_fonction.append(element)
    return specific_dict



def fill_arg(all_args):
    dict = {}
    re_arg = re.compile("([^{]*)=")
    re_mandatory = re.compile("^([^:=,]+)[,]")
    re_defaut = re.compile("[=]([^={]+)")
    for function in all_args:
        dict[str(function[-1])] = {}
        for element in function:
            if re_arg.search(element):
                dict[str(function[-1])][str(re_arg.findall(element)[0])] = {}
                dict[str(function[-1])][str(re_arg.findall(element)[0])]["long"] = str(re_arg.findall(element)[0])

            if re_defaut.search(element):
                dict[str(function[-1])][str(re_arg.findall(element)[0])]["default"] = re_defaut.findall(element)[0]
                if dict[str(function[-1])][str(re_arg.findall(element)[0])]["default"][-1] == ",":
                    dict[str(function[-1])][str(re_arg.findall(element)[0])]["default"] = dict[str(function[-1])][str(re_arg.findall(element)[0])]["default"][0:-1]
            if re_mandatory.search(element):
                dict[str(function[-1])][str(re_mandatory.findall(element)[0])] = {}
                dict[str(function[-1])][str(re_mandatory.findall(element)[0])]["long"] = str(re_mandatory.findall(element)[0])
                #dict[str(function[-1])][str(re_mandatory.findall(element)[0])]["mandatory"] = True
                dict[str(function[-1])][str(re_mandatory.findall(element)[0])]["type"] = "file_in"

    return dict

####################TEST############################
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

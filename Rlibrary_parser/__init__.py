import re
import subprocess
import csv
import yaml as yam
import os
adresse  = "infos.csv"
#adresse  = "monocle_format.R"
#############templates################################
###################Functions and class#######################""
def find_right_type(string):
    """transform R types to click types"""
    if string == 'NULL':
        return 'string'
    if string == '':
        return 'file_in'
    elif string == 'language':
        return 'string'
    elif string == 'double':
        return 'numeric'
    else:
        return string

def better_documentation(function_name, txt_path, csv_reader):
    b = csv.reader(csv_reader)
    arg_list = []
    print("######")
    print(function_name)
    print(txt_path)
    print(csv_reader)
    print("######")
    for element in b:
        print("YUUUP" + str(element))
        arg_list.append(curate_string(element[0]))
        
    print(arg_list)
        




def get_dependencies(texte):
    """get all the dependencies without function specification, output is a list"""
    depend_patern = re.compile("@importFrom ([A-z]+)")
    to_import = depend_patern.findall(texte)
    for element in to_import:
        if to_import.count(element) > 1:
            to_import.pop(to_import.index(element))
    return to_import


def find_documentation(function_name, r_code_path):
    """
    get from a .R the R oxygene (working mostly with seurat type of oxygene)
    """
    with open(r_code_path) as r_code:
        expression = function_name + ' <- '
        r_code = r_code.read()
        splited_txt = r_code.split('\n')
        for element in splited_txt:
            if expression in element:
                line = splited_txt.index(element)
                line = line+1
        oxygene = []
        condition = None
        for k in range(line, 0, -1):
            if '#' in splited_txt[k]:
                condition = True
            if condition and '#' not in splited_txt[k]:
                condition = False
                return(oxygene)
            if condition:
                oxygene.append(splited_txt[k])
  
def curate_string(string):
    """ this function erase most of the special characters from a string """
    string = string.replace(" ","")
    string = string.replace("\n","")
    string = string.replace("#","")
    string = string.replace("}","")
    string = string.replace("{","") 
    string = string.replace("\\","")
    string = string.replace("\'","")
    string = string.replace("`","")
    string = string.replace("\"","")
    string.replace("\r", "\t")
    return string

def curate_string2(string):
    """ this function erase most of the special characters from a string """
    string = string.replace("\n","")
    string = string.replace("#","")
    string = string.replace("}","")
    string = string.replace("{","") 
    string = string.replace("\\","")
    string = string.replace("\'", "")
    string = string.replace("`", "")
    string.replace("\r", "\t")
    return string

def curate_default(string):
    """ This function take a string as input and look for boolean, int , flaot or Null in it, it return the
    corresponding python type """
    boolea1 = re.compile("[T,t][R,r][U,u][E,e]")
    boolea2 = re.compile("[F,f][A,a][L,l][S,s][E,e]")
    inte = re.compile("[0-9]+")
    floa = re.compile("[0-9.[0-9]")
    nul = re.compile("[N,n][U,u][L,l][L,l]")
    if boolea1.match(string):
        return True
    elif boolea2.match(string):
        return False
    elif inte.fullmatch(string):
        return int(string)
    elif floa.fullmatch(string):
        return float(string)
    elif string == '':
        return None
    return string

def curate_type(string):
    """ this function take a string as input and transform it
    Its goal is to take python type and transform it into types used into yaml"""
    if string == "logical":
        return 'boolean'
    if string == 'symbol' or string == 'numeric' or string == 'character':
        return 'string'
    return string

def sort_documentation(arg_name, oxygene):
    is_string = re.compile("[A-z]+")
    if re.search(is_string,arg_name) == None:
        print("sorry element = " + arg_name)        
        return ""
    expression = re.compile("@param ("+arg_name +"[^#]*)")
    output = ""
    for element in oxygene:
        search_object = re.search(expression,element)
        if search_object != None:
            output += search_object.group(1)
            try:   
                index = oxygene.index(element)-1          
                while '@' not in oxygene[index] and index < len(oxygene):
                    sentence_end = oxygene[index].replace("#","")
                    sentence_end = oxygene[index].replace("\'","")
                    output += sentence_end
                    index -= 1
            except:
                pass
    return output
                

ast_func = "r_rlang.R"
#Call R function to go throw the R script and get arguments informations
subprocess.call("dir")


def create_yaml(to_be_wrapped=None, function_name=None, yaml_name="generatedyaml.yaml"):
    """ Take an .R file and the name of the function that we want to wrapp from it as input
        make a yaml file with information need to make the futur wrapper
        /!\ work most of the time with seurat functions BUT the roxygene may not be recognised in other libraries
        steps :
        1) find param names, default values and type if ast_func.R
        2) find documentation with find_documentation function of this module
        3) build a dictionnarie " function_call" that will be dumped in  yaml_name file
        4) dump it

        :param to_be_wrapped: The file location of the .R file
        :type to_be_wrapped: str

        :param function_name: the name of the function we want to wrapp from to_be_wrapped R script
        :type function_name: str

        :param yaml_name: the path of the yaml we will output from this function
        :type yaml_name: str


    """
    #call a R function to_be_wrapped script
    subprocess.call(['Rscript', ast_func, to_be_wrapped, function_name])
    #Open the csv file where the subprocess call stored param name, param default values, param types from the
    with open(adresse) as file:
        a = csv.reader(file)
        function_call = {}
        function_call['call'] = function_name
        #THe documentation is not founded by the subprocess call but by the find_documentation function of this script
        documentation = find_documentation(function_name, to_be_wrapped)
        print("FIND DOCUMENTATION =")
        print(documentation)
        function_call['options'] = []
        #for each param founded in the csv file, start to build the function_call dictionnarie that will be dumped in th efinal yaml file
        for element in a:
            element = element[0].split(';')
            print(element[0])
            #if the param is called return we treat it a special way and put it in
            if curate_string(element[0]) == 'return':
                function_call['output'] = [{'var_name': str(element[2])}]
                continue
            if curate_string(element[0]) == "name":
                continue
            if element[0] == '':
                continue
            else:
                try:
                    arg_infos = {}
                    arg_infos['long'] = curate_string(element[0])
                    arg_infos['default'] = curate_default(curate_string(element[1]))
                    arg_infos['type'] = curate_type(find_right_type(curate_string(element[2])))
                    arg_infos['help'] = curate_string2(sort_documentation(curate_string(element[0]), documentation))
                    print(repr(arg_infos['help']))
                    function_call['options'].append(arg_infos)
                except:
                    pass
        #better_documentation(function_name,to_be_wrapped,file)
    with open(to_be_wrapped) as file:
        txt = file.read()
        commands = {}
        function_call['dependencies'] = get_dependencies(txt)
        commands["commands"] = [function_call]
        print("THIS IS ARGINFOS =    " + str(arg_infos))
    print("THIS IS FUNCTION CALL " + str(function_call))
    with open(yaml_name, "w") as to_fill:
        yam.dump(commands, to_fill)

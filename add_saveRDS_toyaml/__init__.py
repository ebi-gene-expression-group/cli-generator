import yaml 
"""
Add a saveRDS call to a call in a yaml file

"""

def curate_string(string):
    """ this function erase spaces, line jump and '
    """
    string = string.replace("`","")
    string = string.replace(" ","")
    string = string.replace("\n","")
    return string


def modify_all_simple_dict_values(data):
    """recursive function to go through a dictionnary, stops when find a 'var_name' key, and save the var_name in global
    """
    if isinstance(data, dict):
        for k, v in data.items():       
            if 'var_name' in k:
                global var_to_save
                var_to_save = data['var_name']
            if (isinstance(v, dict) or
                isinstance(v, list) or
                isinstance(v, tuple)
                ):
                modify_all_simple_dict_values(v)
            
    elif isinstance(data, list) or isinstance(data, tuple):
        for item in data:
            modify_all_simple_dict_values(item)
    

with open(path) as file:
    docs = yaml.load(file,Loader=yaml.FullLoader)
    modify_all_simple_dict_values(docs)
    #recursivly look for 'var_name' in the dictionnary
    if var_to_save == None:
        print("NO OUTPUT VAR_NAME IN THE YAML")
    else:
        #if var_name key exist, add a new saveRDS call to the dictionnary and then dump it in the original yaml
        to_add = {}
        to_add["call"] = "saveRDS"
        to_add["options"] = [{'long' : 'object', 'type' : 'internal', 'var_name' : curate_string(var_to_save)}, {'long' : 'file', 'type'  : 'file_out'}]
        docs["commands"].append(to_add)
with open(path, "w") as file:    
    yaml.dump(docs, file)

       

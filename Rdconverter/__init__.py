import re
import yaml as yam

def curate_string(string):
    string = string.replace(" ", "")
    return string


def yaml_type(string):
    """ this function take as input the default value of an argument and return the type of it (option_writer)""""
    liste = [
    re.compile("False", re.IGNORECASE),
    re.compile("true", re.IGNORECASE),
    re.compile("[1-9]+"),
    re.compile("[1-9]+\.[1-9]+")
    ]
    correspondance = ['boolean', 'boolean', 'string', 'string']
    for element in liste:
        if element.search(string) != None:
            return correspondance[liste.index(element)]
        else:
            return 'string'

class counting():
"""this class take as self a string starting at the begigning of an argument explanation in a .Rd file :
        \item{argument name }{ help string ..... 
         ....
         end of the .Rd file
    The goal of this counting.count is too find where the help string end and return a raw string of it.
    It is call counting because it counts the { and  } to determine where it ends 
"""    
    def __init__(self, liste, current=1, once=True, help_raw = ''):
        self.current = current
        self.liste = liste
        self.once = once
        self.help_raw = ''

    def count(self):
        for line in self.liste:

            for char in line:
                if not self.once:
                    self.help_raw += char
                    if char == "{":
                        self.current += 1
                if char == "}":
                    self.current -= 1
                if self.current == 0 and not self.once:
                    return self.help_raw
                if self.current == 0 and self.once:
                    self.once = False

def curate_default(string):
    #string = string.replace(r"\\", r"\")
    string = string.replace(" ", "")
    string = string.replace(",", "")
    return string

def curate_string3(string):
    string = string.replace("\n"," ")
    string = string.replace("}","")
    string = string.replace("{","")
    string = string.replace("\\itemize","")
    string = string.replace("\item", "")
    string = string.replace("\code", "")
    return string

def converter(Rdpath):
""" take as input the path to a .Rd file and save a .yaml file """
    with open(Rdpath) as Rdfile:
        Rdtxt = Rdfile.read()
        #Rdtxt = Rdtxt.encode('unicode-escape').decode()
        name = re.search(r'\\name{([^\\]+)}', Rdtxt)
        function_call = {}
        name = name.group(1)
        commands = {}
        commands['commands'] = []
        function_call['call'] = name
        declaration_temp = re.compile(r"\\method{" )
        declaration_area = declaration_temp.findall(Rdtxt)
        if len(declaration_area) > 1:
            declaration_name_temp = re.compile(r'\\method{' + name + r'}{(.+)}')
            declaration_name_list = declaration_name_temp.findall(Rdtxt)
            message = ''
            for element in declaration_name_list:
                message += str(declaration_name_list.index(element)) + ' ' + str(element) + '\n'
            message = "enter the number of the declaration default variables you want : \n" + message + '\n'
            choosen_one = int(input(message))
            if choosen_one > len(declaration_name_list) or choosen_one < 0:
                print('wrong number')
                return 'error'
            choosen_one = str(declaration_name_list[choosen_one])
            print(choosen_one)
            choosen_temp = re.compile(r'\\method\{' + name + r'}\{' + choosen_one + '\}[^\\\]+')
            defaults = choosen_temp.search(Rdtxt)
            defaults = defaults.group(0)
            arg_template = re.compile("(.+)=(.+)")
            defaults = defaults.split('\n')
            option_list = []
            for line in defaults:
                arg_dict = {}
                argument = arg_template.search(line)
                if argument != None:
                    arg_dict['long'] = curate_string(argument.group(1))
                    arg_dict['default'] = curate_default(argument.group(2))
                    arg_dict['type'] = yaml_type(arg_dict['default'])
                    transformed_txt = Rdtxt.split("\n")
                    arg_help_temp = re.compile(r'item\{' + arg_dict['long'])
                    for element in transformed_txt:
                        arg_help = arg_help_temp.search(element)
                        if arg_help != None:
                            a = counting(liste=transformed_txt[transformed_txt.index(element):-1])
                            b = a.count()
                            arg_dict['help'] = curate_string3(b)
                            break
                if arg_dict != {}:
                    option_list.append(arg_dict)
            function_call['options'] = option_list
            function_call['dependencies'] = []
            commands['commands'] = function_call
            with open("fromRd.yaml", "w") as to_fill:
                yam.dump(commands, to_fill)
        else:
            there_is_usage_temp = re.compile(r"\\usage")
            if there_is_usage_temp.search(Rdtxt) == None:
                print(r"CAN NOT FOUND \USAGE")
            else:
                get_usage_temp = re.compile(r"\\usage(.+)\\argument.+ ", re.DOTALL)
                usage = get_usage_temp.search(Rdtxt)
                defaults = usage.group(1)
                arg_template = re.compile("(.+)=(.+)")
                defaults = defaults.split('\n')
                option_list = []
                for line in defaults:
                    arg_dict = {}
                    argument = arg_template.search(line)
                    if argument != None:
                        arg_dict['long'] = curate_string(argument.group(1))
                        arg_dict['default'] = curate_default(argument.group(2))
                        arg_dict['type'] = yaml_type(arg_dict['default'])
                        transformed_txt = Rdtxt.split("\n")
                        arg_help_temp = re.compile(r'item\{' + arg_dict['long'])
                        for element in transformed_txt:
                            arg_help = arg_help_temp.search(element)
                            if arg_help != None:
                                a = counting(liste=transformed_txt[transformed_txt.index(element):-1])
                                b = a.count()
                                arg_dict['help'] = curate_string3(b)
                                break
                    if arg_dict != {}:
                        option_list.append(arg_dict)
                function_call['options'] = option_list
                function_call['dependencies'] = ['workflowscriptscommon','optparse']
                commands['commands'].append(function_call)
                with open("fromRd.yaml", "w") as to_fill:
                    yam.dump(commands, to_fill)




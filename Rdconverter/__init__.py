import re
import yaml as yam

def remove_space(string):
    string = string.replace(" ", "")
    # from G's clean zip
    # why move ) because it tricks the re and think its a group if not
    string = string.replace(")", "[.]")
    string = string.replace("(", "[.]")
    return string


def yaml_type(string):
    """ this function take as input the default value of an argument and return the type of it (option_writer)"""
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

    ...

    :param current: count the number of { and }
    :type current: int
    :param liste: take the option list from the yaml (list)
    :type liste: list
    :param once: True if { was never encountered yet
    :type once: bool
    """
    def __init__(self, liste, current=1, once=True, help_raw = ''):
        self.current = current
        self.liste = liste
        self.once = once
        self.help_raw = ''

    def count(self):
        """
 :param self: list of line from the .Rd
 :type self: list
 :return: a string with all the helpp
        """
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
    """ Take an .Rd file and write most of its informations in a .yaml file

:param Rdpath: The file location of the .Rd file
:type Rdpath: str

    """
    with open(Rdpath) as Rdfile:
        Rdtxt = Rdfile.read()
        #Rdtxt = Rdtxt.encode('unicode-escape').decode()
        name = re.search(r'\\name{([^\\]+)}', Rdtxt)
        #find the name of the function
        function_call = {}
        #create the dictionnary where the call information will be save
        name = name.group(1)
        commands = {}
        commands['commands'] = []
        function_call['call'] = name
        #Search for all \method section in the .Rd
        declaration_temp = re.compile(r"\\method{" )
        declaration_area = declaration_temp.findall(Rdtxt)
        if len(declaration_area) > 1:
            #if there is multiple \method let the user choose which one he wants to put in his yaml
            declaration_name_temp = re.compile(r'\\method{' + name + r'}{(.+)}')
            declaration_name_list = declaration_name_temp.findall(Rdtxt)
            message = ''
            #ask user which \method he wants to put in his yaml
            for element in declaration_name_list:
                message += str(declaration_name_list.index(element)) + ' ' + str(element) + '\n'
            message = "enter the number of the declaration default variables you want : \n" + message + '\n'
            choosen_one = int(input(message))
            if choosen_one > len(declaration_name_list) or choosen_one < 0:
                print('wrong number')
                return 'error'
            choosen_one = str(declaration_name_list[choosen_one])
            choosen_temp = re.compile(r'\\method\{' + name + r'}\{' + choosen_one + '\}[^\\\]+')
            #look for the \method{choosenname}{arg1=default1\n arg2=default2\n ...} template and save it
            defaults = choosen_temp.search(Rdtxt)
            defaults = defaults.group(0)
            #only get arg name and there default to put it in the dictionnary
            arg_template = re.compile("(.+)=(.+)")
            defaults = defaults.split('\n')
            option_list = []
            #organise arg and there default in the dictionnary to make it printable in the yaml
            for line in defaults:
                arg_dict = {}
                argument = arg_template.search(line)
                if argument != None:
                    arg_dict['long'] = remove_space(argument.group(1))
                    arg_dict['default'] = curate_default(argument.group(2))
                    arg_dict['type'] = yaml_type(arg_dict['default'])
                    transformed_txt = Rdtxt.split("\n")
                    # use [1:] because of re parsing problem see: bad escape \s at position error
                    arg_help_temp = re.compile(r'item[.]*' + arg_dict['long'][1:])
                    #run though the .Rd and search where the help template start
                    for element in transformed_txt:
                        arg_help = arg_help_temp.search(element)
                        if arg_help != None:
                            #use counting class to find the end of the help section
                            a = counting(liste=transformed_txt[transformed_txt.index(element):-1])
                            b = a.count()
                            arg_dict['help'] = curate_string3(b)
                            break
                if arg_dict != {}:
                    option_list.append(arg_dict)
            #organise the dictionnary to be .yaml writable
            function_call['options'] = option_list
            function_call['dependencies'] = []
            commands['commands'] = function_call
            #write the yaml file
            with open("fromRd.yaml", "w") as to_fill:
                yam.dump(commands, to_fill)
        else:
            #in this case there is no multiple \method section so we take the entire \usage section to find arg=default
            there_is_usage_temp = re.compile(r"\\usage")
            if there_is_usage_temp.search(Rdtxt) == None:
                print(r"CAN NOT FOUND \USAGE")
            else:
                #search where the \usage{funtction]{arg1=default1\narg2=default2\n...} is and take it
                get_usage_temp = re.compile(r"\\usage(.+)\\argument.+ ", re.DOTALL)
                usage = get_usage_temp.search(Rdtxt)
                defaults = usage.group(1)
                #get arg name and its default to write it in the dictionnary
                arg_template = re.compile("(.+)=(.+)")
                defaults = defaults.split('\n')
                option_list = []
                for line in defaults:
                    arg_dict = {}
                    argument = arg_template.search(line)
                    if argument != None:
                        #write the dictionnary to be .yaml writable
                        arg_dict['long'] = remove_space(argument.group(1))
                        arg_dict['default'] = curate_default(argument.group(2))
                        arg_dict['type'] = yaml_type(arg_dict['default'])
                        transformed_txt = Rdtxt.split("\n")
                        arg_help_temp = re.compile(r'item\{' + arg_dict['long'])
                        for element in transformed_txt:
                            # run though the .Rd and search where the help template start
                            arg_help = arg_help_temp.search(element)
                            if arg_help != None:
                                # use counting class to find the end of the help section
                                a = counting(liste=transformed_txt[transformed_txt.index(element):-1])
                                b = a.count()
                                arg_dict['help'] = curate_string3(b)
                                break
                    if arg_dict != {}:
                        option_list.append(arg_dict)
                # organise the dictionnary to be .yaml writable
                function_call['options'] = option_list
                function_call['dependencies'] = ['workflowscriptscommon','optparse']
                commands['commands'].append(function_call)
                # write the yaml file
                with open("fromRd.yaml", "w") as to_fill:
                    yam.dump(commands, to_fill)




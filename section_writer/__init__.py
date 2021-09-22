from textwrap import dedent
from jinja2 import Template
from option_writer import *


class RSectionWriter:

    def __init__(self, options_dict_list):
        self.options = [ROption.create_option(option) for option in options_dict_list]


class shebang_writer:
    """
    Simply look for the 'shebang' key in the dictionnary and get it
    write() return the shebang string
    """
    def __init__(self, list_of_commands):
        self.shebang = list_of_commands['shebang']
    def write(self):
        return str(self.shebang)


class need_wsc:
    """if default contain a list or a vector, create a call with wsc to treat it
        Care if wsc is needed the variable type is re-writed to internal
        (using need_wsc.corrected_options()) but not in the yaml

        so need_wsc need to be initiated before pre_proc options and need_wsc.write() need to be call
        after option writing
    """
    def __init__(self, list_of_options):
        import re
        self.neednumeric = []
        self.needsplit = []
        self.corrected_options = list_of_options
        numeric_temp  = re.compile("[1-9]+:[1-9]+")
        for option in self.corrected_options:
            if 'default' in option and  option['default'] != None:
                str_default = str(option['default'])
                if ',' in str(str_default):
                    #if ',' in option['default'] it trigger a call for wsc_split_string
                    self.needsplit.append(option['long'])
                    option['var_name'] = option['long']
                    option['type'] = 'internal'
                elif numeric_temp.search(str_default) != None:
                    #if a:b template in option['default'] it trigger a call for wsc_parse_numeric
                    self.neednumeric.append(option['long'])
                    option['var_name'] = option['long']
                    option['type'] = 'internal'
    def write(self):
        """
        return a string with wsc_parse_numeric template
        """
        numeric_temp = Template("""
{% for element in neednumeric %}
    {{ element }} <- wsc_parse_numeric(opt, {{ element }})
{% endfor %}
        """)
        split_temp = Template("""
{% for element in neednumeric %}
   {{ element }} <- wsc_split_string({{ element }}, sep=',')
{% endfor %}
                """)
        return dedent(numeric_temp.render(neednumeric=self.neednumeric) + split_temp.render(needsplit=self.needsplit))



class RsaveRDS:
    """
    Writes the saveRDS section
    """
    def __init__(self, list_of_commands):
        self.needsave = []
        command = list_of_commands[-1]
        if 'output' in command:
            for option in command['options']:
                if option['long'] == 'output_file':
                    self.needsave.append([command['output'][0]['var_name'], True])
                    break
                else:
                    self.needsave.append(command['output'][0]['var_name'])
                    break
    def return_type(self,var):
        #just check is variable is a list
        if type(var) == list:
            return ''
        else:
            return 'no'

    def write(self):
        """
        return a string with the saveRDS template
        """
        save_temp = Template("""
{% for output in needsave %}
    {% if typos(var=output) == '' %}
    saveRDS({{ output }}, file = opt$output_file)
    {% else %}
    saveRDS({{ output }})
    {% endif %}
{% endfor -%}
        """)
        return dedent(save_temp.render(needsave=self.needsave, typos = self.return_type))


class Ropeninglibrary:
    """
    Write the import section for loomR, scater
    """
    def __init__ (self, list_of_options):
        self.needformat = False
        for option in list_of_options:
            if option['long'] == 'input_format':
                #if 'input_format' in one of the option['long'] it trigger the creation of the following section
                self.needformat = True

    def write(self):
        """ write the opening section with loomR or scater library"""
        format_temp = Template("""
{%if needformat %}
    suppressPackageStartupMessages(require(Seurat))
    if(opt$input_format == "loom" | opt$output_format == "loom") {
      suppressPackageStartupMessages(require(loomR))
    } else if(opt$input_format == "singlecellexperiment" | opt$output_format == "singlecellexperiment") {
      suppressPackageStartupMessages(require(scater))
    }    
{% endif %}
        """)
        return dedent(format_temp.render(needformat=self.needformat))



class RDependencies:
    """
    Writes the dependency section for R
    """
    def __init__(self, list_of_commands):
        self.dependencies = set()
        for command in list_of_commands:
            if 'dependencies' in command:
                self.dependencies.update(command['dependencies'])

    def write(self):
        deps_t = Template("""
{% for dep in dependencies -%}
suppressPackageStartupMessages(require({{ dep }}))
{% endfor -%}
        """)

        return dedent(deps_t.render(dependencies=self.dependencies))


class ROptionsDeclarationWriter(RSectionWriter):

    def write_declarations(self):
        make_calls = list()
        mandatory = list()
        for option in self.options:
            write = True
            for other_option in self.options:
                if option == other_option:
                    continue
                if str(option._long()) == str(other_option._long()):
                    write = False
            if not write:
                print("WARNING SAME - LONG USED MULTIPLE TIME CHECK THE .yaml : " + str(option._long()))
                self.options.pop(self.options.index(option))
                continue
            if option.is_declarable:
                make_calls.append(option.option_maker())
                if not option.has_default:
                    mandatory.append(option.long_value())

        make_calls_t = Template("""
option_list <- list(
{%- for call in calls -%}
    {%- if not loop.last %}
    {{ call }},
    {%- else %}
    {{ call }}
    {%- endif -%}
{%- endfor %})

opt <- wsc_parse_args(option_list, 
                      mandatory = c({%- for m in mandatory -%}{%- if not loop.last -%}"{{ m }}", {% else -%}"{{ m }}"{%- endif -%}{%- endfor -%} ))
                """)
        return dedent(make_calls_t.render(calls=[call for call in make_calls if call],
                                          mandatory=mandatory))


class RPreprocessWriter(RSectionWriter):

    def write_preprocess(self):
        #pre_process_calls = [option.pre_process() for option in self.options if option.has_preprocess]
        pre_process_calls = []
        for option in self.options:
            if option.has_preprocess:
                pre_process_calls.append(option.pre_process())
                pre_process_calls_t = Template("""
{%- for call in calls %}
{{ call }}
{% endfor -%}
                """)
        return dedent(pre_process_calls_t.render(calls=pre_process_calls))



class RCommandWriter(RSectionWriter):

    def __init__(self, command, **kwargs):
        super().__init__(**kwargs)
        self.command = command
        # self.options = list()
        # self._create_options_list(options_dict_list)

    @staticmethod
    def create_writer(command):
        if 'output' in command:
            return RSingleResultCommandWriter(command=command['call'],
                                                  options_dict_list=command['options'],
                                                  output=command['output'][0]['var_name'])
        return RCommandWriter(command=command['call'],
                             options_dict_list=command['options'])

    # def _create_options_list(self, options_dict_list):
    #    for option in options_dict_list:
    #        self.options.append(ROption.create_option(option_dict=option))

    def write_command_call(self):
        command_t = Template("""
{{ command }}(
    {%- for param_call in param_calls -%}
                    {% if not loop.last -%}
                    {{ param_call }},
                    {% else -%}                            
                    {{ param_call }}
                    {%- endif %}
    {%- endfor %})
        """)

        param_calls = list()
        for option in self.options:
            param_calls.append(option.option_caller())
        return dedent(command_t.render(command=self.command,
                                       param_calls=param_calls,
                                       ))


class RSingleResultCommandWriter(RCommandWriter):

    def __init__(self, output, **kwargs):
        super().__init__(**kwargs)
        self.output = output

    def write_command_call(self):
        command_t = Template("""
{{ output }} <- {{ command }}(
    {%- for param_call in param_calls -%}
                    {% if not loop.last -%}
                    {{ param_call }},
                    {% else -%}
                    {{ param_call }}
                    {%- endif %}
    {%- endfor %})
        """)

        param_calls = list()
        for option in self.options:
            param_calls.append(option.option_caller())
        return dedent(command_t.render(command=self.command,
                                       param_calls=param_calls,
                                       output=self.output
                                       ))


class GalaxySectionWriter:
    def __init__(self, options_dict_list):
        self.options = [GalaxyOption.create_option(option) for option in options_dict_list
                        if GalaxyOption.create_option(option) is not None]


class GalaxyOptionsDeclarationWriter(GalaxySectionWriter):

    def write_declarations(self):

        inputs_t = Template("""
                <inputs>
                {%- for option in i_options %}
                    {{ option.option_maker() }}
                {%- endfor %} 
                </inputs>
        """)

        outputs_t = Template("""
                <outputs>
                {%- for option in o_options %}
                    {{ option.option_maker() }}
                {%- endfor %}
                </outputs>
        """)

        result = dedent(inputs_t.render(
            i_options=[option for option in self.options if isinstance(option, GalaxyInputOption)]))

        result += dedent(outputs_t.render(
            o_options=[option for option in self.options if isinstance(option, GalaxyOutputOption)]))

        return result


class GalaxyCommandWriter(GalaxySectionWriter):

    def write_command(self):

        command_t = Template(
            """
            <command detect_errors="exit_code"><![CDATA[
                {%- for option in options -%}
                    {{ option.option_caller() }}
                {%- endfor %}    
            ]]</command>
            """)

        command = dedent(command_t.render(options=self.options))
        return command

from textwrap import dedent
from jinja2 import Template
from option_writer import *


class RSectionWriter:

    def __init__(self, options_dict_list):
        self.options = [ROption.create_option(option) for option in options_dict_list]

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
                                      mandatory = c({%- for m in mandatory -%}{%- if not loop.last -%}'{{ m }}',{%- else -%}'{{ m }}'{%- endif -%}{%- endfor -%} ))
                """)
        return dedent(make_calls_t.render(calls=[call for call in make_calls if call],
                                          mandatory=mandatory))


class RPreprocessWriter(RSectionWriter):

    def write_preprocess(self):
        pre_process_calls = [option.pre_process() for option in self.options if option.has_preprocess]

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

import os.path
from textwrap import dedent, indent
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
            if 'default' in option and option['default'] is not None:
                str_default = str(option['default'])
                if ',' in str(str_default):
                    # if ',' in option['default'] it trigger a call for wsc_split_string
                    self.needsplit.append(option['long'])
                    option['var_name'] = option['long']
                    option['type'] = 'internal'
                elif numeric_temp.search(str_default) is not None:
                    # if a:b template in option['default'] it trigger a call for wsc_parse_numeric
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
        # just check is variable is a list
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
                # if 'input_format' in one of the option['long'] it trigger the creation of the following section
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
            if not option.is_declarable:
                continue
            for other_option in self.options:
                if option == other_option:
                    continue
                if str(option._long()) == str(other_option._long()):
                    print(f"WARNING: {option._long()} long used multiple times, "
                          f"declaring only once. Check the .yaml if unintended")
                    other_option.is_declarable = False
            make_calls.append(option.option_maker())
            if not option.has_default:
                mandatory.append(option.long_value())

        make_calls_t = Template("""
option_list <- list(
{% for call in calls %}
    {% if not loop.last %}
    {{ call }},
    {% else %}
    {{ call }}
    {% endif %}
{% endfor %})

opt <- wsc_parse_args(option_list, 
                      mandatory = c({%- for m in mandatory -%}{%- if not loop.last -%}"{{ m }}", {% else -%}"{{ m }}"{%- endif -%}{%- endfor -%} ))
                """, trim_blocks=True, lstrip_blocks=True)
        return make_calls_t.render(calls=[call for call in make_calls if call],
                                          mandatory=mandatory)


class RPreprocessWriter(RSectionWriter):

    def write_preprocess(self):
        # pre_process_calls = [option.pre_process() for option in self.options if option.has_preprocess]
        pre_process_calls = []
        pre_process_calls_t = None
        for option in self.options:
            if option.has_preprocess:
                pre_process_calls.append(option.pre_process())
                pre_process_calls_t = Template("""
{%- for call in calls %}
{{ call }}
{% endfor -%}
                """)
        if pre_process_calls_t:
            return dedent(pre_process_calls_t.render(calls=pre_process_calls))
        else:
            return ""


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
        if 'rcode' in command:
            return RCodeWriter(code=command['rcode'])
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


class RCodeWriter:

    def __init__(self, code):
        self.code = code

    def write_command_call(self):
        return dedent(self.code)


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
        self.existing = None
        self.options = [GalaxyOption.create_option(option) for option in options_dict_list
                        if GalaxyOption.create_option(option) is not None]

    def _recover_manual_entry(self, manual_from_file, section=None):
        """
        Recovers into self.existing a section within a given Galaxy XML file
        that is surrounded by
        
        <!-- MANUAL {section} -->
            some content
        <!-- END MANUAL {section} -->
        
        Initially introduced for facilitating writing helps and tests on the written XML.
        
        This assumes that there is a single block within the document that responds to that pattern
        :param manual_from_file: usually the same XML file that we are writing.
        :param section: either HELP or TESTS currently
        """
        if not os.path.isfile(manual_from_file):
            return
        comment_start = "<!-- "
        self.existing = ""
        print(f"Reading manual {section} from {manual_from_file}")
        with open(file=manual_from_file) as f:
            save_lines = False
            for line in f:
                if f"{comment_start}MANUAL {section}" in line:
                    save_lines = True
                if save_lines:
                    self.existing = self.existing + line
                if f"{comment_start}END MANUAL {section}" in line:
                    save_lines = False
        self.existing = indent(dedent(self.existing.rstrip('\n')), prefix="  ")

    def _define_macros(self, macro_mapper=None):
        self.macro = {}
        for macro_type in self.MACROS:
            self.macro[macro_type] = []

        # look for options that map to macros
        for group in macro_mapper:
            if set(group['option_group']).issubset([str(option) for option in self.options]):
                # add macros
                [self.macro[macro_type].extend(group[macro_type])
                 for macro_type in self.MACROS if macro_type in group]
                # remove the options now that they have been replaced by macros
                to_rm_options = [opt for opt in self.options if str(opt) in group['option_group']]
                for rm_opt in to_rm_options:
                    self.options.remove(rm_opt)


class GalaxyOptionsDeclarationWriter(GalaxySectionWriter):

    INPUT_DECLARATION_MACROS = 'input_declaration_macros'
    OUTPUT_DECLARATION_MACROS = 'output_declaration_macros'

    MACROS = [INPUT_DECLARATION_MACROS, OUTPUT_DECLARATION_MACROS]

    def __init__(self, options_dict_list, macro_mapper=[]):
        super(GalaxyOptionsDeclarationWriter, self).__init__(options_dict_list)
        self._define_macros(macro_mapper)
        self.advanced_options = [option for option in self.options if 'advanced' in option.elements]
        if self.advanced_options:
            for adv_o in self.advanced_options:
                self.options.remove(adv_o)

    def write_declarations(self):

        inputs_t = Template(dedent(
                """
                <inputs>
                {% for input_macro in i_dec_macros %}
                    {% if input_macro is mapping %}
                    <expand macro="{{ input_macro.keys() | first }}" 
                    {%- for i_macro in input_macro %}
                    {% for token in input_macro[i_macro] %} {{ token }}="{{ input_macro[i_macro][token] }}" {% endfor %} {% endfor -%} /> 
                    {% else %}
                    <expand macro="{{ input_macro }}" />
                    {% endif %}
                {% endfor %}
                {% for option in i_options %}
                    {{ option.option_maker() }}
                {% endfor %} 
                {% if i_adv_options %}
                    <section name="adv" title="Advanced options">
                    {% for adv_option in i_adv_options %}
                        {{ adv_option.option_maker() }}
                    {% endfor %}
                    </section>
                {% endif %}
                </inputs>
                """), lstrip_blocks=True, trim_blocks=True)

        outputs_t = Template(dedent(
                """
                <outputs>
                {% for output_macro in o_dec_macros %}
                    <expand macro="{{ output_macro }}"/>
                {% endfor %}
                {% for option in o_options %}
                    {{ option.option_maker() }}
                {% endfor %}
                </outputs>
                """), lstrip_blocks=True, trim_blocks=True)

        result = inputs_t.render(
            i_options=[option for option in self.options if isinstance(option, GalaxyInputOption)],
            i_adv_options=[option for option in self.advanced_options if isinstance(option, GalaxyInputOption)],
            i_dec_macros=self.macro[self.INPUT_DECLARATION_MACROS])

        result += outputs_t.render(
            o_options=[option for option in self.options if isinstance(option, GalaxyOutputOption)],
            o_dec_macros=self.macro[self.OUTPUT_DECLARATION_MACROS])

        return result


class GalaxyHeaderWriter:
    """
    Writer for the <tool ..>, <description /> and initial macros
    """

    def __init__(self, id, name, profile="18.01",
                 version="1.0", description="",
                 macros=[], macro_expands_header=[],
                 macro_expands_footer=[]
                 ):
        self.tool_id = id
        self.tool_name = name
        self.tool_description = description
        self.profile = profile
        self.version = version
        self.macros = macros
        self.macro_expands = macro_expands_header

    def write(self):
        header_t = Template(dedent(
            """\
            <tool id="{{ tool_id }}" name="{{ tool_name }}" profile="{{ profile }}" version="{{ version }}+galaxy0">
                <description>{{ tool_description }}</description>
                {% if macros %}
                {% for macro in macros %}
                <macros>
                    <import>{{ macro }}</import>
                </macros>
                {% endfor %}
                {% for expand in macro_expands %}
                <expand macro="{{expand}}" />
                {% endfor %}
                {% endif %}
            """
        ), lstrip_blocks=True, trim_blocks=True)

        result = header_t.render(tool_id=self.tool_id, tool_name=self.tool_name,
                                 profile=self.profile, version=self.version, tool_description=self.tool_description,
                                 macros=self.macros, macro_expands=self.macro_expands
                                 )

        return result


class GalaxyFooterWriter:
    """
    Writer for the </tool> and closing macros
    """

    def __init__(self, macro_expands_footer=[]):
        self.macro_expands = macro_expands_footer

    def write(self):
        footer_ = Template(dedent(
            """
                {% for expand in macro_expands %}
                <expand macro="{{expand}}" />
                {% endfor %}
            </tool>
            """
        ), lstrip_blocks=True, trim_blocks=True)

        return footer_.render(macro_expands=self.macro_expands)


class GalaxyCommandWriter(GalaxySectionWriter):

    PRE_COMMAND_MACROS = 'pre_command_macros'
    POST_COMMAND_MACROS = 'post_command_macros'

    MACROS = [PRE_COMMAND_MACROS, POST_COMMAND_MACROS]

    def __init__(self, options_dict_list, command=None, macro_mapper=[]):
        super(GalaxyCommandWriter, self).__init__(options_dict_list)
        self._define_macros(macro_mapper)
        self._command = command

    def write_command(self):

        command_t = Template(dedent(
            """\
            <command detect_errors="exit_code"><![CDATA[
            {% for pre_cmd_macro in pre_cmd_macros %}
            @{{ pre_cmd_macro }}@
            {% endfor %}
            {{ cli_command }}
            {% for post_cmd_macro in post_cmd_macros %}
            @{{ post_cmd_macro }}@
            {% endfor %}
            {% for option in options %}
            {{ option.option_caller() }}
            {% endfor %}    
            ]]></command>
            """), lstrip_blocks=True, trim_blocks=True)

        command = command_t.render(options=self.options,
                                   cli_command=self._command,
                                   pre_cmd_macros=self.macro[self.PRE_COMMAND_MACROS],
                                   post_cmd_macros=self.macro[self.POST_COMMAND_MACROS])
        return command


class GalaxyTestWriter(GalaxySectionWriter):

    def __init__(self, manual_from_file=None):
        super(GalaxyTestWriter, self).__init__([])
        if manual_from_file:
            self._recover_manual_entry(manual_from_file, section="TESTS")

    def write(self):
        test_t = Template(dedent(
            """
            <tests>
            {% if manual %}
            {{ manual }}\
            {% endif %} 
            </tests>\
            """), lstrip_blocks=True, trim_blocks=True)

        return test_t.render(manual=self.existing)


class GalaxyHelpWriter(GalaxySectionWriter):

    def __init__(self, manual_from_file=None):
        super(GalaxyHelpWriter, self).__init__([])
        if manual_from_file:
            self._recover_manual_entry(manual_from_file, section='HELP')

    def write(self):
        content = ""
        if self.existing:
            content = self.existing
        help_t = Template(dedent(
            """
            <help>
            {% if manual %}
            {{ manual }}\
            {% endif %} 
            </help>\
            """), lstrip_blocks=True, trim_blocks=True)

        return help_t.render(manual=dedent(content))





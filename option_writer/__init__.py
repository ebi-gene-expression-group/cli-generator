from textwrap import dedent
from jinja2 import Template
import copy
import logging


class Option:

    def __init__(self, dict_with_slots):
        self.elements = copy.deepcopy(dict_with_slots)
        self.has_preprocess = False
        self.is_declarable = True
        self.has_default = 'default' in self.elements

    @staticmethod
    def create_option(option_dict):
        """
        Factory method to intialise options based on the contents of the
        option dictionary provided.

        :param option_dict:
        :return:
        """
        for field in ['long', 'type']:
            if field not in option_dict:
                print(option_dict)
                raise Exception("Option is invalid, {} field is required.".format(field))

    def option_caller(self):
        """
        Defines how the option is used within the library usage (script).
        :return:
        """
        pass

    def option_maker(self):
        """
        Defines how the option is created inside the scripts that call the library
        methods.
        :return:
        """
        pass

    def pre_process(self):
        pass

    def _human_readable(self):
        if 'human_readable' not in self.elements:
            return self.elements['long'].capitalize().replace(".", " ")
        return self.elements['human_readable']

    def _long(self):
        return self.elements['long']

    def long_value(self):
        return self.elements['long']

    def _type(self):
        return self.elements['type']

    def _help(self):
        try:
            return self.elements['help']
        except:
            return 'FILE IN'

    def _default(self):
        return self.elements['default']

    def is_optional(self):
        return 'optional' in self.elements and self.elements['optional']

    def __str__(self):
        return self.elements['long']


class BooleanOption(Option):
    """
    Base class for Boolean Options across frameworks
    """
    def _long(self):
        if self.elements['default']:
            return "do-not-{}".format(self.elements['long'])
        else:
            return self.elements['long']


class ROption(Option):
    """
    Base class for R OptParse options
    """
    def __init__(self, r_separator=".", **kwargs):
        super().__init__(**kwargs)
        self.r_sep = r_separator

    @staticmethod
    def create_option(option_dict, aliases_dict=None):
        super(ROption, ROption).create_option(option_dict=option_dict)

        if option_dict['type'] == 'string' and "evaluated" in option_dict and option_dict['evaluated']:
            return EvaluatedROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'string':
            return CharacterROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'string_or_file':
            return RDSFileOrStringInputROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'boolean':
            return BooleanROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'file_in':
            return FileInputROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'file_out':
            return FileROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'list':
            return StringListOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'internal':
            return InternalVarROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'integer':
            return IntegerROption(dict_with_slots=option_dict)
        if option_dict['type'] == 'double':
            return DoubleROption(dict_with_slots=option_dict)
        else:
            print(f"Option type {option_dict['type']} is not recognised...")
            exit(1)

    def option_maker(self):
        """
        Produces a text for creating the option in optparse
            make_option(
                c('-i', '--input-file'),
                action='store',
                default=NULL,
                metavar='Input file',
                type='character',
                help='The input file for...'
            )
        :return: text as specified
        """
        maker_t = Template(dedent("""\
            make_option(
                    c("{{ flags }}"),
                    action = "{{ action }}",
                    {% if 'default' in elements %}
                    default = {{ default }},
                    {% endif %}
                    {% if 'human_readable' in elements %}
                    metavar = "{{ human_readable }}",
                    {% endif %}
                    type = "{{ type }}",
                    help = "{{ help }}"
                )
            """), trim_blocks=True, lstrip_blocks=True)

        output = maker_t.render(flags=self._short_and_long(),
                                action=self._action(),
                                default=self._default(),
                                human_readable=self._human_readable(),
                                type=self._type(),
                                help=self._help(),
                                elements=self.elements,
                                )
        return output

    def option_caller(self):
        """
        Produces the text for invoking the option within the library function call.
        :return: text of the form 'my.option = opt$my_option'
        """
        return "{} = {}".format(self.library_arg(), self._option_variable())

    def _option_variable(self):
        return f"opt${self.long_value()}"

    def _short_and_long(self):
        if 'short' in self.elements and 'long' in self.elements:
            return "-{}\", \"--{}".format(self.elements['short'], self._long().replace(".", "-"))
        elif 'short' in self.elements:
            return "-{}".format(self.elements['short'])
        elif 'long' in self.elements:
            return "--{}".format(self._long().replace(".", "-"))
        else:
            raise Exception("Option needs to have at least short or long defined")

    def library_arg(self):
        """
        The library argument should be the exact name that the library expects
        for the argument. If for some reason the cli option cannot match the
        library option/argument, then you can use an alias:

        - long: input-format
          call_alias: format

        in this case the cli will receive an `--input-format` argument which will
        be mapped to `format` for the library call.

        In the case of R a cli argument `--pca-dimensions` will be accepted by some
        R libraries as `pca.dimensions`, so this method allow for those changes (and
        aliasing).
        :return: The argument name as expected by the library, for command calling prep.
        """
        if 'call_alias' in self.elements:
            return self.elements['call_alias'].replace("-", self.r_sep)
        return self.elements['long'].replace("-", self.r_sep)

    def long_value(self):
        return self.elements['long'].replace("-", "_").replace(".", "_")

    def _action(self):
        return 'store'

    def _default(self):
        if 'default' not in self.elements:
            return None
        if self.elements['default'] is None:
            return "NULL"
        if self.elements['default'] == 'NULL':
            return "NULL"
        if isinstance(self.elements['default'], int) or isinstance(self.elements['default'], float):
            return self.elements['default']
        return f"\"{self.elements['default']}\""


class InternalVarROption(ROption):
    """
    Represents and internal R variable available to the library call that doesn't
    need to be consumed from the cli options, but that is generated by some other
    process/command in the script. As such, it needs not making, default nor help,
    but only calling.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_declarable = False

    def option_maker(self):
        return None

    def _option_variable(self):
        if 'value' in self.elements:
            return self.elements['value']
        return self.elements['var_name']


class CharacterROption(ROption):
    """
    Base class for anything that it is a character option in R.
    """
    def _type(self):
        return 'character'


class DoubleROption(ROption):
    def _type(self):
        return 'double'


class IntegerROption(ROption):
    def _type(self):
        return 'integer'


class FileROption(CharacterROption):
    pass


class FileInputROption(FileROption):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_preprocess = True

    def pre_process(self):
        """
        Produce code that checks whether the file exists or not.
        :return:
        """

        file_exists_t = Template("""
        if (!file.exists({{ path }})) {
            stop((paste("File", {{ path }}, "does not exist")))
        }
        """)
        output = file_exists_t.render(path=self._option_variable())

        return dedent(output)


class RDSFileOrStringInputROption(CharacterROption):
    """
    Case for options that need to be treated as a file or as a string, depending on what is provided.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_preprocess = True

    def pre_process(self):
        """
        Check if the given option is a file or a string, and read accordingly leaving on the same variable for use
        :return:
        """

        file_or_string_t = Template("""
        if (!is.na(as.numeric({{ variable }}))) {
            # this case also covers variables that can accept a numeric entry, but if the number is passed as a string
            # the R method can often fail with unspecific errors.
            {{ variable }} <- as.numeric({{ variable }})
        } else if (file.exists({{ variable }})) {
            # if the file exists, then we load it, otherwise the variable keeps its content.
            tmp <- readRDS({{ variable }})
            {{ variable }} <- tmp
        }
        """)
        output = file_or_string_t.render(variable=self._option_variable())

        return dedent(output)


class BooleanROption(BooleanOption, ROption):
    """
    A boolean option for OptParse in R

    If the default is true, then the flag should indicate a false state
    """
    def option_caller(self):
        if self.elements['default']:
            return "{} = opt${}".format(self.library_arg(), self._long().replace("-", "_").replace(".","_"))
        else:
            return super(BooleanROption, self).option_caller()

    def _action(self):
        if self.elements['default']:
            return "store_false"
        else:
            return "store_true"

    def _type(self):
        return "logical"

    def _default(self):
        if self.elements['default']:
            return "TRUE"
        else:
            return "FALSE"


class EvaluatedROption(CharacterROption):
    """
    Useful for cases such as dims = 1:30 or dims = c(1,2,30), which need to be evaluated. They will come as inputs
    like text "1:30" or "1,3,5" and then need to be evaluated in R to be used.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_preprocess = True

    def pre_process(self):
        """
        Produce code to evaluate in R as an expression
        :return:
        """

        evaluate_t = Template("""
        if (!is.null({{ option_var }})) {
            {{ option_var }} <- eval(parse(text = {{ option_var }}))
        }
        """)

        output = evaluate_t.render(long_value=self.long_value(),
                                   option_var=self._option_variable())

        return dedent(output)


class StringListOption(CharacterROption):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_preprocess = True

    def option_caller(self):
        """
        On string list, input is processed and left in variable of same name as
        self._long_arg()
        :return: text of the form 'my.option = opt$my_option'
        """
        return "{} = {}".format(self.library_arg(), self.long_value())

    def pre_process(self, tok_fun_name="unlist(strsplit({}, sep = \",\"))"):
        """
        Produce code to tokenize list into parts
        :param tok_fun_name: the call to be used to untokenize.
        :return:
        """

        tokenise_t = Template("""
        {{ long_value }} <- {{ option_var }}
        if (!is.null({{ long_value }})) {
            {{ long_value }} <- {{ tok_fun }}
        }
        """)

        output = tokenise_t.render(long_value=self.long_value(),
                                   option_var=self._option_variable(),
                                   tok_fun=tok_fun_name.format(self._option_variable())
                                   )

        return dedent(output)


class GalaxyOption(Option):
    """
    Base Galaxy option class
    """
    def long_value(self, prefix_advanced: bool = False):
        lv = self.elements['long'].replace("-", "_").replace(".", "_")
        if prefix_advanced:
            if 'advanced' in self.elements and self.elements['advanced']:
                lv = f"adv.{lv}"
        return lv

    def long_call(self):
        return self._long().replace(".", "-")

    def option_caller(self):
        caller_t = Template(dedent(
            """
            {% if optional %}
            #if ${{ long_value }}
            {% endif %}
            --{{ long }} '${{ long_value }}'
            {% if optional %}
            #end if
            {% endif %}
            """), lstrip_blocks=True, trim_blocks=True)

        return caller_t.render(long=self.long_call(), long_value=self.long_value(True), optional=self.is_optional())

    def _help(self):
        """
        Takes help, but replacing " for ' to avoid issues in the Galaxy help field.
        :return:
        """
        if 'help' in self.elements:
            return self.elements['help'].replace("\"", "'")
        else:
            logging.warning(f"Element {self._long()} has no help!")


    @staticmethod
    def create_option(option_dict, aliases_dict=None):
        super(GalaxyOption, GalaxyOption).create_option(option_dict=option_dict)

        if option_dict['type'] in ['string', 'integer', 'float']:
            if 'options' in option_dict:
                return GalaxySelectOption(dict_with_slots=option_dict)
            else:
                return GalaxyInputOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'string_or_file':
            return FileOrStringGalaxyInputOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'boolean':
            return BooleanGalaxyOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'file_in':
            return FileInputGalaxyOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'file_out':
            return GalaxyOutputOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'internal':
            return None


class GalaxyInputOption(GalaxyOption):
    """
    Base Galaxy input option class
    """
    def option_maker(self):
        """
        Produces a text for creating the option in Galaxy
            <param label="Features" optional="true" name="features" argument="--features" type="text" help="Comma-separated list of genes to use for building SNN."/>
        :return: text as specified
        """
        maker_t = Template("""<{{ tag }} label="{{ label }}" {{ optional_default }} name="{{ name }}" """ +
                           """argument="--{{ argument }}" type="{{ type }}" {{ format }} """ +
                           """{{ boolean }} help="{{ help }}"/>""")

        output = maker_t.render(
                                tag=self._tag(),
                                label=self._human_readable(),
                                optional_default=self._galaxy_default_declaration(),
                                name=self.long_value(prefix_advanced=True),
                                argument=self.long_call(),
                                type=self._type(),
                                format=self._galaxy_format_declaration(),
                                help=self._help(),
                                boolean=self._boolean_declare()
                                )
        return dedent(output)

    def _tag(self):
        return "param"

    def _boolean_declare(self):
        return ""

    def _type(self):
        if super()._type() == 'string':
            return 'text'
        return super()._type()

    def _galaxy_default_declaration(self):
        if self.has_default and str(self._default()) != "'NULL'":
            return "optional='true' value='{}'".format(str(self._default()).replace("'", ""))
        elif self.is_optional():
            return "optional='true'"
        return ""

    def _galaxy_format_declaration(self):
        return ""

    def _default(self):
        if 'default' not in self.elements:
            return None
        if self.elements['default'] is None:
            return ""
        return "'{}'".format(self.elements['default'])


class GalaxySelectOption(GalaxyInputOption):

    def get_options_hash(self):
        """
        Transforms:

        default: thirdOption
        options:
          - firstOption
          - secondOption: Second option
          - thirdOption

        into
         options_hash = { 'firstOption': 'firstOption',
                          'secondOption': "Second Option",
                          'thirdOption': 'thirdOption'
                          }
        :return:
        """
        result = {}
        for option in self.elements['options']:
            if type(option) is dict:
                for opt_key in option:
                    result[opt_key] = option[opt_key]
            else:
                result[option] = option

        return result

    def get_options_selected_hash(self):
        """
        Transforms:

        default: thirdOption
        options:
          - firstOption
          - secondOption: Second option
          - thirdOption

        into
          selection_text = { 'firstOption': "",
                             'secondOption': "",
                             'thirdOption': ' selected="true"'
                            }
        :return:
        """
        result = {}
        for option in self.elements['options']:
            if type(option) is dict:
                for opt_key in option:
                    if self.elements['default'] == opt_key:
                        result[opt_key] = ' selected="true"'
                    else:
                        result[opt_key] = ''
            else:
                if self.elements['default'] == option:
                    result[option] = ' selected="true"'
                else:
                    result[option] = ''

        return result

    """
    Galaxy option with select
    """
    def option_maker(self):
        """
        Produces a text for creation a select galaxy option
        <param name="norm" argument="--normalization-method" type="select" optional="True" label="Normalisation method" help = "Method for normalization. Default is log-normalization (LogNormalize). Can be 'CLR' or 'RC' additionally.">
          <option value="LogNormalize" selected="true">Log Normalise</option>
          <option value="CLR">CLR</option>
          <option value="RC">RC</option>
        </param>
        :return:
        """
        maker_t = Template(dedent(
            """\
            <{{ tag }} label="{{ label }}" name="{{ name }}" argument="--{{ argument }}" type="select" {{ format }} help="{{ help }}">
            {% for option in options %}
                    <option value="{{ option }}"{{ selected[option] }}>{{ options[option] }}</option>
            {% endfor %}
                </{{ tag }}>
            """), lstrip_blocks=True, trim_blocks=True)

        output = maker_t.render(
            tag=self._tag(),
            label=self._human_readable(),
            selected=self.get_options_selected_hash(),
            options=self.get_options_hash(),
            name=self.long_value(prefix_advanced=True),
            argument=self.long_call(),
            help=self._help()
        )

        return output


class BooleanGalaxyOption(BooleanOption, GalaxyInputOption):
    """
    Galaxy boolean option writer, handles
    """
    def option_caller(self):
        return "${}\n".format(self.long_value(prefix_advanced=True))

    def _boolean_declare(self):
        """
        Used to define the truevalue, falsevalue and checked status
        in the option declaration.
        :return:
        """
        if self.elements['default']:
            truevalue = ""
            checked = "true"
            falsevalue = "--{}".format(self.long_call())
        else:
            truevalue = "--{}".format(self.long_call())
            checked = "false"
            falsevalue = ""

        declare_t = Template("truevalue='{{ truevalue }}' falsevalue='{{ falsevalue }}' checked='{{ checked }}'")

        return declare_t.render(truevalue=truevalue, checked=checked, falsevalue=falsevalue)

    def _type(self):
        return "boolean"

    def _default(self):
        if self.elements['default']:
            return "true"
        else:
            return "false"


class FileInputGalaxyOption(GalaxyInputOption):

    def _type(self):
        return "data"

    def _galaxy_format_declaration(self):
        return "format='{}'".format(self.elements['format'] if 'format' in self.elements else "?")


class FileOrStringGalaxyInputOption(GalaxyInputOption):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_option = FileInputGalaxyOption(dict_with_slots=self.elements)
        self._string_option = GalaxyInputOption(dict_with_slots=self.elements)
        self._file_option.elements['long'] = self._file_option.elements['long'] + "_file"
        self._file_option.elements['help'] = f"File option for {self._string_option.elements['long']}. " \
                                             f"This overrides the string option if set."


    def option_maker(self):
        """
        Adds an option for the file (which overrides the string) and one for the string, used instead if the file is
        not defined.
        :return:
        """

        maker_t = Template(dedent(
            """{{ file_option }}
                {{ string_option }}
            """), lstrip_blocks=True, trim_blocks=True)

        return maker_t.render(file_option=self._file_option.option_maker(),
                                string_option=self._string_option.option_maker()
                                )

    def option_caller(self):
        """
        Produces the call of the joint options so that if the file is set, it has priority over the string.
        :return:
        """
        caller_t = Template(dedent(
            """
            #if ${{ long_value_file }}
            --{{ long_string }} '${{ long_value_file }}'
            {% if optional %}
            #elif ${{ long_value_string }}
            {% else %}
            #else
            {% endif %}
            --{{ long_string }} '${{ long_value_string }}'
            #end if
            """), lstrip_blocks=True, trim_blocks=True)

        return caller_t.render(long_string=self._string_option.long_call(),
                               long_value_string=self._string_option.long_value(True),
                               long_value_file=self._file_option.long_value(True),
                               optional=self.is_optional())



class GalaxyOutputOption(GalaxyOption):

    def option_maker(self):
        """
        Produces a text for creating the output in Galaxy
            <data format="pdf" name="output_1" label="\$\{tool.name\} on \$\{on_string\}: out" argument="--features" type="text" help="Comma-separated list of genes to use for building SNN."/>
        :return: text as specified
        """
        maker_t = Template("""<{{ tag }} label="${tool.name} on ${on_string}: {{ label }}" """ +
                           """name="{{ name }}" """ +
                           """{{ format }} />""")

        output = maker_t.render(
            tag=self._tag(),
            label=self._human_readable(),
            name=self.long_value(),
            format=self._galaxy_format_declaration(),
        )
        return dedent(output)

    def _galaxy_format_declaration(self):
        return "format='{}'".format(self.elements['format'] if 'format' in self.elements else "?")

    def _tag(self):
        return "data"
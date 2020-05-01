from textwrap import dedent
from jinja2 import Template


class Option:

    def __init__(self, dict_with_slots):
        self.elements = dict_with_slots
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
            return self.elements['long'].capitalize()
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


class BooleanOption(Option):
    """
    Base class for Boolean Options accross frameworks
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

        if option_dict['type'] == 'string':
            return CharacterROption(dict_with_slots=option_dict)
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
        maker_t = Template("""make_option(
                    c('{{ flags }}'),
                    action='{{ action }}',
                    {% if 'default' in elements -%}
                    default={{ default }},
                    {% endif -%}
                    {% if 'human_readable' in elements -%}
                    metavar='{{ human_readable }}',
                    {% endif -%}
                    type='{{ type }}',
                    help='{{ help }}')
                    """)

        output = maker_t.render(flags=self._short_and_long(),
                                action=self._action(),
                                default=self._default(),
                                human_readable=self._human_readable(),
                                type=self._type(),
                                help=self._help(),
                                elements=self.elements,
                                )
        return dedent(output)

    def option_caller(self):
        """
        Produces the text for invoking the option within the library function call.
        :return: text of the form 'my.option = opt$my_option'
        """
        return "{} = {}".format(self.library_arg(), self._option_variable())

    def _option_variable(self):
        return "opt${}".format(self.long_value())

    def _short_and_long(self):
        if 'short' in self.elements and 'long' in self.elements:
            return "-{}','--{}".format(self.elements['short'], self._long())
        elif 'short' in self.elements:
            return "-{}".format(self.elements['short'])
        elif 'long' in self.elements:
            return "--{}".format(self._long())
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
        return self.elements['long'].replace("-", "_")

    def _action(self):
        return 'store'

    def _default(self):
        if 'default' not in self.elements:
            return None
        if self.elements['default'] is None:
            return "NULL"
        return "'{}'".format(self.elements['default'])


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
        if ( ! file.exists({{ path }}) ) {
            stop((paste('File', {{ path }}, 'does not exist')))
        }
        """)
        output = file_exists_t.render(path=self._option_variable())

        return dedent(output)


class BooleanROption(BooleanOption, ROption):
    """
    A boolean option for OptParse in R

    If the default is true, then the flag should indicate a false state
    """
    def option_caller(self):
        if self.elements['default']:
            return "{} = !opt${}".format(self.library_arg(), self._long().replace("-", "_"))
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

    def pre_process(self, tok_fun_name="unlist(strsplit({}, sep=','))"):
        """
        Produce code to tokenize list into parts
        :param tok_fun_name: the call to be used to untokenize.
        :return:
        """

        tokenise_t = Template("""
        {{ long_value }} <- {{ option_var }}
        if (! is.null({{ long_value }}) ) {
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
    def option_maker(self):
        """
        Produces a text for creating the option in Galaxy
            <param label="Features" optional="true" name="features" argument="--features" type="text" help="Comma-separated list of genes to use for building SNN."/>
        :return: text as specified
        """
        maker_t = Template("""<param label="{{ label }}" {{ optional_default }} name="{{ name }}" """ +
                           """argument="--{{ argument }}" type="{{ type }}" {{ format }} """ +
                           """{{ boolean }} help="{{ help }}"/>""")

        output = maker_t.render(
                                label=self._human_readable(),
                                optional_default=self._galaxy_default_declaration(),
                                name=self.long_value(),
                                argument=self._long(),
                                type=self._type(),
                                format=self._galaxy_format_declaration(),
                                help=self._help(),
                                boolean=self._boolean_declare()
                                )
        return dedent(output)

    def _boolean_declare(self):
        return ""

    def long_value(self):
        return self.elements['long'].replace("-", "_")

    def option_caller(self):
        caller_t = Template("""
        #if ${{ long_value }}
            --{{ long }} '${{ long_value }}'
        #end if
        """)

        return dedent(caller_t.render(has_default=self.has_default,
                                      long_value=self.long_value(),
                                      long=self._long()))

    @staticmethod
    def create_option(option_dict, aliases_dict=None):
        super(GalaxyOption, GalaxyOption).create_option(option_dict=option_dict)

        if option_dict['type'] == 'string':
            return GalaxyOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'boolean':
            return BooleanGalaxyOption(dict_with_slots=option_dict)
        if option_dict['type'] == 'file_in':
            return FileInputGalaxyOption(dict_with_slots=option_dict)
        # if option_dict['type'] == 'file_out':
        #     return FileROption(dict_with_slots=option_dict)
        # if option_dict['type'] == 'list':
        #     return StringListOption(dict_with_slots=option_dict)
        # if option_dict['type'] == 'internal':
        #     return InternalVarROption(dict_with_slots=option_dict)

    def _type(self):
        if super()._type() == 'string':
            return 'text'
        return super()._type()

    def _galaxy_default_declaration(self):
        if self.has_default:
            return "optional='true' value='{}'".format(self._default().replace("'", ""))

    def _galaxy_format_declaration(self):
        return ""

    def _default(self):
        if 'default' not in self.elements:
            return None
        if self.elements['default'] is None:
            return ""
        return "'{}'".format(self.elements['default'])


class BooleanGalaxyOption(BooleanOption, GalaxyOption):
    """
    Galaxy boolean option writer, handles
    """
    def option_caller(self):
        return "${{{}}}".format(self.long_value())

    def _boolean_declare(self):
        """
        Used to define the truevalue, falsevalue and checked status
        in the option declaration.
        :return:
        """
        if self.elements['default']:
            truevalue = ""
            checked = "true"
            falsevalue = "--{}".format(self._long())
        else:
            truevalue = "--{}".format(self._long())
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

#class FileInputGalaxyOption(GalaxyOption):

#    def _galaxy_format_declaration(self):


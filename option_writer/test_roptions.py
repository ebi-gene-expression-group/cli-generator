from option_writer import *

sample_option_simple_string = {
    'long': 'my-string-var',
    'short': 'm',
    'type': 'string',
    'human_readable': 'My string var',
    'help': 'This is important for proces xyz',
    'default': "hello-world"
}

sample_option_simple_string_maker = """make_option(
                    c('-m','--my-string-var'),
                    action='store',
                    default='hello-world',
                    metavar='My string var',
                    type='character',
                    help='This is important for proces xyz')
"""

sample_option_simple_string_caller = "my.string.var = opt$my_string_var"


def test_write_string_option():
    opt = ROption.create_option(sample_option_simple_string)
    assert opt.option_maker() == sample_option_simple_string_maker
    assert opt.option_caller() == sample_option_simple_string_caller


sample_option_boolean_false = {
    'long': 'my-logical-var',
    'type': 'boolean',
    'human_readable': 'My logical var',
    'help': 'This is important for proces xyz',
    'default': False
}

sample_option_boolean_false_maker = """make_option(
                    c('--my-logical-var'),
                    action='store_true',
                    default=FALSE,
                    metavar='My logical var',
                    type='logical',
                    help='This is important for proces xyz')
"""

sample_option_boolean_false_caller = "my.logical.var = opt$my_logical_var"


def test_write_boolean_option():
    opt = ROption.create_option(sample_option_boolean_false)
    assert opt.option_maker() == sample_option_boolean_false_maker
    assert opt.option_caller() == sample_option_boolean_false_caller


sample_option_boolean_true = {
    'long': 'my-logical-var',
    'type': 'boolean',
    'human_readable': 'My logical var',
    'help': 'This is important for proces xyz',
    'default': True
}

sample_option_boolean_true_maker = """make_option(
                    c('--do-not-my-logical-var'),
                    action='store_false',
                    default=TRUE,
                    metavar='My logical var',
                    type='logical',
                    help='This is important for proces xyz')
"""

sample_option_boolean_true_caller = "my.logical.var = !opt$do_not_my_logical_var"


def test_write_boolean_true_option():
    opt = ROption.create_option(sample_option_boolean_true)
    assert opt.option_maker() == sample_option_boolean_true_maker
    assert opt.option_caller() == sample_option_boolean_true_caller


sample_option_file_in = {
    'long': 'my-file-var',
    'short': 'f',
    'type': 'file_in',
    'human_readable': 'File input',
    'help': 'This is important for proces xyz'
}

sample_option_file_in_maker = """make_option(
                    c('-f','--my-file-var'),
                    action='store',
                    metavar='File input',
                    type='character',
                    help='This is important for proces xyz')
"""

sample_option_file_in_caller = "my.file.var = opt$my_file_var"

sample_option_file_in_exists = """
if ( ! file.exists(opt$my_file_var) ) {
    stop((paste('File', opt$my_file_var, 'does not exist')))
}
"""


def test_write_file_in_option():
    opt = ROption.create_option(sample_option_file_in)
    assert opt.option_maker() == sample_option_file_in_maker
    assert opt.option_caller() == sample_option_file_in_caller
    assert opt.pre_process() == sample_option_file_in_exists


sample_option_list = {
    'long': 'dimensions-list',
    'short': 'd',
    'type': 'list',
    'separator': ',',
    'dest_type': 'int',
    'human_readable': 'Dimensions for pca',
    'help': "Comma separated list of dimensions for PCA",
    'default': "1,2"
}

sample_option_list_maker = """make_option(
                    c('-d','--dimensions-list'),
                    action='store',
                    default='1,2',
                    metavar='Dimensions for pca',
                    type='character',
                    help='Comma separated list of dimensions for PCA')
"""

sample_option_list_tokenizer = """
dimensions_list <- opt$dimensions_list
if (! is.null(dimensions_list) ) {
    dimensions_list <- unlist(strsplit(opt$dimensions_list, sep=','))
}
"""

sample_option_list_caller = "dimensions.list = dimensions_list"


def test_write_list():
    opt = ROption.create_option(sample_option_list)
    assert opt.option_maker() == sample_option_list_maker
    assert opt.pre_process() == sample_option_list_tokenizer
    assert opt.option_caller() == sample_option_list_caller


sample_internal = {
    'long': 'object',
    'type': 'internal',
    'var_name': 'seurat_object'
}


def test_internal():
    opt = ROption.create_option(sample_internal)
    assert opt.option_maker() is None
    assert opt.option_caller() == "object = seurat_object"


response_galaxy_option_simple_string_call="""
#if $my_string_var
    --my-string-var '$my_string_var'
#end if
"""

response_galaxy_option_simple_string_make="""<param label="My string var" optional='true' value='hello-world' name="my_string_var" argument="--my-string-var" type="text"   help="This is important for proces xyz"/>"""


def test_galaxy_option():
    opt = GalaxyInputOption.create_option(sample_option_simple_string)
    assert opt.option_maker() == response_galaxy_option_simple_string_make
    assert opt.option_caller() == response_galaxy_option_simple_string_call

response_galaxy_option_boolean_true_make="""<param label="My logical var" optional='true' value='true' name="my_logical_var" argument="--do-not-my-logical-var" type="boolean"  truevalue='' falsevalue='--do-not-my-logical-var' checked='true' help="This is important for proces xyz"/>"""
response_galaxy_option_boolean_true_call="${my_logical_var}"


def test_boolean_galaxy_option():
    opt = GalaxyInputOption.create_option(sample_option_boolean_true)
    assert opt.option_maker() == response_galaxy_option_boolean_true_make
    assert opt.option_caller() == response_galaxy_option_boolean_true_call

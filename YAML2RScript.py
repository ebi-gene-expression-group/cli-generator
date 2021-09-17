import yaml
from section_writer import *
from RWrapperOrganiser import *
import argparse

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-i', '--input-yaml',
                        required=True,
                        help='YAML file with instructions')
arg_parser.add_argument('-o', '--output',
                        required=True,
                        help='RScript output')
args = arg_parser.parse_args()


with open(file=args.input_yaml) as f:
    script_data = yaml.load(f)

all_opts = list()
for command in script_data['commands']:
    all_opts.extend(command['options'])

dep_w = RDependencies(script_data['commands'])

opt_w = ROptionsDeclarationWriter(all_opts)

preproc_w = RPreprocessWriter(all_opts)

commands = ""
for command in script_data['commands']:
    cmd_w = RCommandWriter.create_writer(command)
    commands += cmd_w.write_command_call()

write_R_file(args.output, dep_w.write(), opt_w.write_declarations(), preproc_w.write_preprocess(), commands)

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
                        help='Galaxy wrapper output')
arg_parser.add_argument('-m', '--macro-mapper',
                        help="YAML mappings for options to macros")
args = arg_parser.parse_args()

with open(file=args.input_yaml) as f:
    script_data = yaml.safe_load(f)

macro_mapper = []
if args.macro_mapper:
    with open(file=args.macro_mapper) as f:
        macro_mapper = yaml.safe_load(f)

all_opts = list()
for command in script_data['commands']:
    if 'rcode' in command:
        continue
    all_opts.extend(command['options'])

cli_command = None
if 'cli_call' in script_data:
    cli_command = script_data['cli_call']
opt_c = GalaxyCommandWriter(all_opts, command=cli_command, macro_mapper=macro_mapper)
print(opt_c.write_command())

opt_w = GalaxyOptionsDeclarationWriter(all_opts, macro_mapper=macro_mapper)
print(opt_w.write_declarations())
import yaml
from section_writer import *
from RWrapperOrganiser import *
from carousel import RCarousel
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
carousels = []

all_commands = []

for command in script_data['commands']:
    if 'rcode' in command:
        all_commands.append(command)
        continue
    if 'call_carousel' in command:
        carousel = RCarousel(command)
        all_opts.extend(carousel.get_options())
        carousels.append(carousel)
        all_commands.extend(carousel.get_commands())
        continue
    all_opts.extend(command['options'])
    all_commands.append(command)


dep_w = RDependencies(all_commands)

opt_w = ROptionsDeclarationWriter(all_opts)

preproc_w = RPreprocessWriter(all_opts)

commands = ""
for command in all_commands:
    cmd_w = RCommandWriter.create_writer(command)
    commands += cmd_w.write_command_call()

# get the entire command for reproducibility - this should be refactored into a class
import sys
command = " ".join(sys.argv)
message = f"""
# This script has been automatically generated through
#
# {command}
#
# to change this file edit the input YAML and re-run the above command
"""

write_R_file(args.output,
             message,
             dep_w.write(),
             opt_w.write_declarations(),
             preproc_w.write_preprocess(),
             commands)

# make script executable for the user
import os
import stat

st = os.stat(args.output)
os.chmod(args.output, st.st_mode | stat.S_IEXEC)


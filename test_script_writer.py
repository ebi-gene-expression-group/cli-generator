
import os
import yaml
from section_writer import *
from RWrapperOrganiser import *
from textwrap import dedent

TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'findtransferanchors.yaml')


def test_script_writing():
    with open(file=TESTDATA_FILENAME) as f:
        script_data = yaml.full_load(f)
    to_be_writed = []
    all_opts = list()
    for command in script_data['commands']:
        all_opts.extend(command['options'])
    print("ALL OPTS = " + str(all_opts))

    shebang_w = shebang_writer(script_data)
    to_be_writed.append(shebang_w.write())

    dep_w = RDependencies(script_data['commands'])
    print("ALLL DEPENDENCIES ")
    print(dep_w.write())
    to_be_writed.append(dep_w.write())

    save_w = RsaveRDS(script_data['commands'])
    print(save_w.write())

    wsc_treatment = need_wsc(all_opts)
    all_opts = wsc_treatment.corrected_options

    opt_w = ROptionsDeclarationWriter(all_opts)
    print(opt_w.write_declarations())
    to_be_writed.append(opt_w.write_declarations())

    to_be_writed.append(wsc_treatment.write())

    try:
        preproc_w = RPreprocessWriter(all_opts)
        print(preproc_w.write_preprocess())
        to_be_writed.append(preproc_w.write_preprocess())
    except:
        pass


    importformat_w = Ropeninglibrary(all_opts)
   # to_be_writed.append(importformat_w.write())

    for command in script_data['commands']:
        cmd_w = RCommandWriter.create_writer(command)
        print(cmd_w.write_command_call())
        to_be_writed.append(cmd_w.write_command_call())

    to_be_writed.append(save_w.write())
    with open("R_file.R", 'w+') as r_file:

        for element in to_be_writed:
            r_file.write(dedent(element))

    

test_script_writing()


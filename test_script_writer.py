import os
import yaml
from section_writer import *
from RWrapperOrganiser import * 

#TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'PercentageFeatureSet.yaml')
TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'yo.yaml')

def test_script_writing():   
    with open(file=TESTDATA_FILENAME) as f:
        script_data = yaml.full_load(f)
        all_opts = list()
        for command in script_data['commands']:
            print("here it is \n \n " + str(command))      
            try:
                all_opts.extend(command['options'])
            except:
                pass
        print("bbb =  " + str(all_opts))
        dep_w = RDependencies(script_data['commands'])
        print(dep_w.write())

        opt_w = ROptionsDeclarationWriter(all_opts)
        print(opt_w.write_declarations())
       
        preproc_w = RPreprocessWriter(all_opts)
        print(all_opts)
        print(preproc_w.write_preprocess())
        
        for command in script_data['commands']:
            cmd_w = RCommandWriter.create_writer(command)
            print(cmd_w.write_command_call())
        create_R_file(dep_w.write(), opt_w.write_declarations(),preproc_w.write_preprocess(), cmd_w.write_command_call())    

test_script_writing()


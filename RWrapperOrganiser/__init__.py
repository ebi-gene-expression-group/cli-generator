import inspect

def create_R_file(*args,**kwargs):
    with open("R_file.R", 'r+') as r_file:
        to_write = r_file.read()
        all_args = inspect.getfullargspec(create_R_file)
        a = (locals()[all_args[1]])
        gafa = ' '.join(str(k) for k in a)
        r_file.write(to_write)
            
            
        
    
    

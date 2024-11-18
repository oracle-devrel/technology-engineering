import argparse

PROGVERSION="270924"

def main():
    print("constantMaker version:"+PROGVERSION)
    args_parser = argparse.ArgumentParser(description="beautyfier")
    args_parser.add_argument("--infile",default=None,type=str,help="input list")
    args_parser.add_argument("--outfile",default=None,type=str,help="output python module name")
    args_parser.add.argument("--constatsfile",default=None,type=str,help="inputfile with consants, separated by =")
    args_parser.add_argument("--type",default='py',type=str,help="py|update")
    args = args_parser.parse_args()
#
    if args.infile is None or args.outfile is None:
        print("Usage: --infile <list of constants> --outfile python_module --scriptfile bashscript to change the content of source")
        exit(1)

    if not (args.type.lower() == 'py' or args.type.lower() == 'update'):
        print("type needs to be either 'py' or 'update'. 'py' creates constant file, 'update' updates file from constants ")
        exit(1)

    if args.infile.lower() == 'update ':
        if args.consantsfile is None :
            print("Infile and outfile both need proper value")
            print("Usage: --infile <list of constants> --outfile python_module --scriptfile bashscript to change the content of source")
            exit(1)
    # Open infile
    with open(args.infile,'r') as infile:
        lines = infile.read().splitlines()
    # open outfile
    outfile=open(args.outfile,'w')
    #
    if args.type == 'py':
        outfile.write('#\n# (c) Inge Os 2024\n# Constants for bastionsession.py\n#\n')
    else:
        # type update
        with open(args.parse.constantfile) as cfile:
            lines = cfile.read().splitlines()
        constants={}
        while line in lines:
            line=line.strip('\n')
            constant=line.split('=')
            constants[constant[0]]=constant[1]
    for line in lines:
        if args.type == 'py':
            lastfield=line.rstrip('\n')
            firstfield=lastfield.replace('"','').upper()+'='+(lastfield)
            outfile.write(firstfield+'\n')
        else:
            '''
            lastfield=line.strip('\n').split('=')[1].strip(' ')
            firstfield=line.strip('\n').split('=')[1].strip(' ')
            outfile.write("TEMP=`echo $TEMP | sed 's/"+firstfield+"/"+lastfield+"/'`\n")
            '''
            print('Line:: '+line)
            for key in constants:
                if line.find(key):
                    line.replace(key,constants[key])
                    print('Replace: '+line)
    outfile.close()




if __name__ == "__main__":
    main()

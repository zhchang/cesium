import os
import sys
import urllib
import platform
import subprocess
import logging
from sets import Set


def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def exit(why):
    print why
    sys.exit(1)


def get_system():
    return (platform.system(), platform.architecture()[0])


def run_shell(args, **kwargs):
    p = subprocess.Popen(args)
    r, e = p.communicate()
    if kwargs.get('raiseError', False) and e is not None:
        raise e
    return r


system = ()
osinfo = {}

os_info = {
    'Linux2': {
        'protoc': {
            '32bit': 'https://github.com/google/protobuf/releases/download/v3.0.2/protoc-3.0.2-linux-x86_32.zip',
            '64bit': 'https://github.com/google/protobuf/releases/download/v3.0.2/protoc-3.0.2-linux-x86_64.zip',
        },
    },
    'Darwin': {
        'protoc': {
            '32bit': 'https://github.com/google/protobuf/releases/download/v3.0.2/protoc-3.0.2-osx-x86_32.zip',
            '64bit': 'https://github.com/google/protobuf/releases/download/v3.0.2/protoc-3.0.2-osx-x86_64.zip',
        },
    },
}

protoc_dir = 'protoc-dir'
protoc_file = 'protoc.zip'


def setup_protoc():
    gopath = os.environ['GOPATH']
    gopathbin = os.path.join(gopath, 'bin')

    print 'I see you dont have protoc yet, setting up...'
    try:
        run_shell(['rm', '-rf', protoc_dir])
        urllib.urlretrieve(osinfo['protoc'][system[1]], protoc_file)
        print 'downloaded, unzipping '
        run_shell(['unzip', '-d', protoc_dir, protoc_file], raiseError=True)
        target = os.path.join(gopathbin, 'protoc')
        print 'coping to %s' % (target)
        run_shell(['cp', protoc_dir + '/bin/protoc', target], raiseError=True)
        print 'protoc shall be good to use now'
    except Exception as e:
        exit('man I failed to play with protoc. can you setup on your own and talk to me again when you are done. error: %s' % (e))
    finally:
        try:
            run_shell(['rm', '-rf', protoc_dir])
            run_shell(['rm', '-f', protoc_file])
        except:
            pass
    if which('protoc') is not None:
        print 'protoc setup ok'
    else:
        exit('man I failed to play with protoc. can you setup on your own and talk to me again when you are done.')


server_template = '''
// {server-name} defines impl of grpc server
type {server-name} struct{
}
'''
api_template = '''
// {api-name} impls grpc server handler interface
func (*{server-name}) {api-name}(ctx context.Context, request *pb.{api-request})(*pb.{api-reply}, error){
    // TODO: implement this API
}
'''


def can_write(path):
    print 'validating ' + path
    try:
        with open(path, 'w'):
            return True
    except:
        return False


def output_to_file(what, content):
    try:
        output = ask_until_right('where do you want to write %s to?' % (what), [
            'quit'], can_write)
        with open(output, 'w') as f:
            f.write(content)
            print 'done writing to that.'
    except:
        print 'I ll print to stdout then'
        print content


def gen_server(name, members):
    name += 'Impl'
    generated = server_template.replace('{server-name}', name)
    for member in members:
        api = api_template
        api = api.replace('{api-name}', member['name'])
        api = api.replace('{server-name}', name)
        api = api.replace('{api-request}', member['request'])
        api = api.replace('{api-reply}', member['reply'])
        generated += api
    output_to_file('server impl', generated)


method_template = '''
// {api-name} do rpc call
func {api-name}(ctx context.Context, cc *grpc.ClientConn, in *pb.{request-type}, opts ...grpc.CallOption)(*pb.{reply-type}, error){
    return New{client-name}(cc).{api-name}(ctx, in, opts)
}
'''


def gen_client(name, members):
    generated = ''
    for member in members:
        api = method_template.replace('{api-name}', member['name'])
        api = api.replace('{client-name}', name)
        api = api.replace('{request-type}', member['request'])
        api = api.replace('{reply-type}', member['reply'])
        generated += api
    output_to_file('client impl', generated)


def parse_api(line, types):
    api = {}
    api['name'] = line[:line.find('(')]
    items = line.split(' ')
    for item in items:
        m1 = item.find('*')
        if m1 != -1:
            payload = item[m1 + 1:]
            if payload.find(',') != -1:
                payload = payload[:payload.find(',')]
            elif payload.find(')') != -1:
                payload = payload[:payload.find(')')]
            if payload in types:
                if 'request' not in api:
                    api['request'] = payload
                elif 'reply' not in api:
                    api['reply'] = payload

    return api


def parse_types(path):
    types = Set()
    with open(path, 'r') as f:
        for line in f.xreadlines():
            line = line.rstrip()
            if line.find('type ') == 0:
                items = line.split(' ', 4)
                if items[2] == 'struct' and not items[1][0].islower():
                    types.add(items[1])
    return types


def parse_pbgo(path):
    types = parse_types(path)
    blocks = {}
    flag = 'searching'
    running_block = []
    running_key = ''
    valid_block = False
    with open(path, 'r') as f:
        for line in f.xreadlines():
            line = line.rstrip()
            if flag == 'searching':
                if line.find('type ') == 0:
                    items = line.split(' ', 4)
                    running_key = items[1]
                    valid_block = items[2] == 'interface'
                    running_block = []
                    flag = 'reading'
            elif flag == 'reading':
                if line.find('}') == 0:
                    flag = 'searching'
                    if valid_block:
                        blocks[running_key] = running_block
                    running_key = ''
                    running_block = []
                else:
                    line = line.strip()
                    if line.find('//') != 0:
                        running_block.append(parse_api(line, types))
    for name, members in blocks.iteritems():
        if name[-6:] == 'Server':
            gen_server(name, members)
        elif name[-6:] == 'Client':
            gen_client(name, members)

    return blocks


def check_env():
    global system, osinfo
    system = get_system()
    if system[0] not in os_info:
        exit('man, you are using some unsupported system.')
    osinfo = os_info[system[0]]
    if which('go') == None:
        exit('bro, please install go first!')

    if 'GOPATH' not in os.environ or len(os.environ['GOPATH']) == 0:
        exit('maybe you have not set you gopath correctly?')

    path = os.environ['PATH']
    gopath = os.environ['GOPATH']
    gopathbin = os.path.join(gopath, 'bin')

    if path.find(gopathbin) is None:
        print 'gopath/bin not found in path, adding that.'
        os['PATH'] = gopathbin + ':' + path

    if which('protoc') == None:
        setup_protoc()


def ask(prompt, choices):
    suffix = '[' + '/'.join(choices) + ']?'
    while True:
        choice = raw_input(prompt + suffix)
        if choice in choices:
            return choice
        print 'dude, I mean ' + suffix


def ask_until_right(prompt, quit_list, validator):
    while True:
        if len(quit_list) > 0:
            reply = raw_input('%s type %s to quit\n' % (prompt, quit_list))
        else:
            reply = raw_input(prompt)
        if reply in quit_list:
            raise Exception('quit')
        if validator(reply):
            return reply
        print 'I dont think that works. maybe we should try again.'


if __name__ == '__main__':
    check_env()

    if len(sys.argv) == 1:
        print 'I have done what I can. Bye.'
        sys.exit(0)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        try:
            input_file = ask_until_right('where is the .proto file?', [
                'gg', 'no', 'stop'], os.path.exists)
        except:
            exit('ok then.')
    target_path = os.path.dirname(input_file)
    if target_path == '':
        target_path = '.'
    output_file = input_file[:-5] + 'pb.go'
    try:
        run_shell(['protoc', '-I', target_path, '--go_out=plugins=grpc:%s' % (target_path),
                   input_file], raiseError=True)
        print('I did a good job generating pb.go. Now analysing the file')
        parse_pbgo(output_file)
        sys.exit(0)
    except Exception as e:
        logging.exception('bro, something really wrong')

import os
import sys
import urllib
import platform
import subprocess


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


if __name__ == '__main__':
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

    if len(sys.argv) == 1:
        print 'I have done what I can. Bye.'
        sys.exit(0)

    input_file = sys.argv[1]
    while True:
        if not os.path.exists(input_file):
            choice = raw_input(
                'I dont think %s exists, care to give me another one?[Y/N]' % (input_file))
            if choice == 'Y' or choice == 'y':
                input_file = raw_input('tell me then:')
            else:
                exit('ok dude, later.')
        else:
            break
    target_path = os.path.dirname(input_file)
    try:
        run_shell(['protoc', '-I', target_path, '--go_out=plugins=grpc:%s' % (target_path),
                   input_file], raiseError=True)
        print('I did a good job.')
        sys.exit(0)
    except Exception as e:
        exit('bro, I tried. QQ :  %s' % (e))

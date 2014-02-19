import sys, os
from binascii import hexlify
import paramiko


class AskUserPolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        print "The authenticity of host '%s' can't be established." % hostname
        print "The %s key fingerprint is %s." %\
              (key.get_name(), format(key.get_fingerprint()))
        if query_yes_no('Do you want to trust the host?'):
            client._host_keys.add(hostname, key.get_name(), key)
            client.save_host_keys(client._host_keys_filename)


def format(fingerprint):
    line = hexlify(fingerprint)
    n = 2
    return ':'.join([line[i:i+n] for i in range(0, len(line), n)])


def query_yes_no(question, default="no"):
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")


def ssh(host):
    p = host.find(':')
    if p >= 0:
        port = host[p+1:]
        host = host[:p]
    else:
        port = 22
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
    ssh.known_hosts = os.path.expanduser('~/.ssh/known_hosts')
    ssh.set_missing_host_key_policy(AskUserPolicy())
    try:
        ssh.connect(host, port, '', '')
    except paramiko.AuthenticationException:
        pass
    except paramiko.SSHException:
        pass


if __name__ == '__main__':
    fname = os.path.expanduser('~/.ssh')
    if not os.path.exists(fname):
        os.mkdir(fname)
    fname = os.path.expanduser('~/.ssh/known_hosts')
    if not os.path.exists(fname):
        with open(fname, 'a'):
            pass
    ssh(sys.argv[1])

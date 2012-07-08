from fabric import api as fapi
from fabric.state import env

from arghandler import ArgHandler

import string

class PyMurder:
    def __init__(self, argDict):
        self.args = ArgHandler(argDict)
        pass

    def create_torrent(self, tag, files_path):
        trackers = self.args.getHosts('tracker')

        tracker_host = trackers[0]
        tracker_port = self.args.trackerPort()

        filename = "/tmp/%s.tgz" % tag
        seeder_files_path = files_path

        self.exec_all([
            ('run', "tar -c -z -C %s/ -f %s --exclude \".git*\" ." %
                (seeder_files_path, filename)),
            ('run', "python %s/murder_make_torrent.py '%s' %s:%i '%s.torrent'" %
                (self.args.remoteMurderPath(),filename,tracker_host,tracker_port,filename))],
                ['seeder'])

        self.download_torrent(tag)

    def download_torrent(self, tag):
        filename = "/tmp/%s.tgz" % tag

        self.exec_all([
            ('get', "%s.torrent" % filename, "%s.torrent" % filename)],
            ['seeder'])

    def start_seeding(self, tag):
        filename = "/tmp/%s.tgz" % tag

        self.exec_all([
            ('run', 
            "SCREENRC=/dev/null SYSSCREENRC=/dev/null screen -dms"
            " 'seeder-%s' python %s/murder_client.py seeder '%s.torrent' '%s'"
            " `LC_ALL=C host ${PYMURDER_HOST} | awk '/has address/ {print $$4}'"
            "| head -n 1` && sleep 0.2" % (tag, self.args.remoteMurderPath(), filename, filename))],
            ['seeder'], use_shell=True)

    def stop_seeding(self, tag):
        self.pkill_roles("SCREEN.*seeder-%s" % (tag), ['seeder'])

    def stop_peering(self, tag):
        filename = "/tmp/%s.tgz" % tag
        self.pkill_roles("pkill -f \"murder_client.py peer.*%s\"" % (filename), ['peer'])

    def clean_temp_files(self, tag):
        filename = "/tmp/%s.tgz" % tag
        self.exec_all([(run, "rm -rf %s %s.torrent || exit 0" % (filename, filename))], ['peer'])

    def start_peering(self, tag, destination_path):
        filename = "/tmp/%s.tgz" % tag

        hosts = self.args.getHosts('peer')

        args = dict(self.args.args)

        for host in hosts:
            env.host_string = host

            with fapi.settings(**args):
                fapi.run("mkdir -p %s/" % (destination_path))
                fapi.run("find '%s/'* >/dev/null 2>&1 && echo \"destination_path"
                         " %s on $HOSTNAME is not empty\" && exit 1 || exit 0" % (destination_path,
                            destination_path))
                fapi.put("%s.torrent" % (filename), "%s.torrent" % (filename))
                fapi.run("python %s/murder_client.py peer"
                         " '%s.torrent' '%s' `LC_ALL=C host"
                         " %s | awk '/has address/ {print $4}' | head -n 1`" % 
                         (self.args.remoteMurderPath(), filename, filename, host))
                fapi.run("tar xf %s -C %s" % (filename, destination_path))

    def distribute_files(self):
        hosts = self.args.getHosts('tracker', 'seeder', 'peer')

        fapi.local("tar -c -z -C %s -f\
                /tmp/murder_dist_to_upload.tgz ." % (self.args.distPath()))

        args = dict(self.args.args)

        for host in hosts:
            env.host_string = host

            with fapi.settings(**args):
                fapi.run("mkdir -p %s/" % self.args.remoteMurderPath())
                fapi.run("[ $(find '%s/'* | wc -l ) -lt 1000 ] && rm -rf '%s/'* || "
                        "(echo 'Cowardly refusing to remove files! Check the "
                        "remote_murder_path.' ; exit 1 )" %\
                        (self.args.remoteMurderPath(),\
                            self.args.remoteMurderPath()))
                fapi.put("/tmp/murder_dist_to_upload.tgz", "/tmp/murder_dist.tgz")
                fapi.run("tar xf /tmp/murder_dist.tgz -C %s" %\
                        (self.args.remoteMurderPath()))
                fapi.run("rm /tmp/murder_dist.tgz")

        fapi.local("rm /tmp/murder_dist_to_upload.tgz")

    def start_tracker(self):
        self.exec_all([('run', "SCREENRC=/dev/null SYSSCREENRC=/dev/null screen -dms"
                               " murder_tracker python %s/murder_tracker.py && sleep 0.2" %
                (self.args.remoteMurderPath()))], ['tracker'], use_shell=True)

    def stop_tracker(self):
        self.pkill_roles('SCREEN.*murder_tracker.py', ['tracker'])

    def stop_all_seeding(self):
        self.pkill_roles('SCREEN.*seeder-*', ['seeder'])

    def stop_all_peering(self):
        self.pkill_roles('murder_client.py.peer*', ['peer'])

    def exec_all(self, commands, roles, **kwargs):
        hosts = self.args.getHosts(*roles)

        args = dict(self.args.args)
        args.update(kwargs)

        for host in hosts:
            env.host_string = host

            with fapi.settings(**args):
                for command in commands:
                    type = command[0]

                    if 'run' == type:
                        tpl = string.Template(command[1])
                        cmd = tpl.substitute(PYMURDER_HOST=host)
                        fapi.run(cmd)
                    elif 'get' == type:
                        fapi.get(command[1], command[2])

    def pkill_roles(self, name, roles):
        hosts = self.args.getHosts(*roles)

        args = dict(self.args.args)

        for host in hosts:
            env.host_string = host

            with fapi.settings(**args):
                self.pkill(name)

    def pkill(self, name):
        fapi.run("ps -ef | grep %s | grep -v grep | awk '{print $2}' |"
                 " xargs kill || echo 'no process with name %s found'" % (name,name))

Quick and dirty API port of murder (https://github.com/lg/murder/) to python 
by Amir Elaguizy <aelaguiz@gmail.com>.

This does not attempt to implement the executable version, instead it is a 
simple API that may be used from within python applications.

This is dependent upon the python fabric module. 

DISCLAIMER
----------
This is a reasonably faithful port for a half day job, but it isn't complete.
I ported all commands but left some of the flags/behavior modifying pieces out
because I did not need them. A full port would include addition of support
for all of the modifiers such as 'path_is_file' and 'no_tag_directory', etc.

This also desperately needs proper packaging, I hope to come back and do this
but time is short.

DESCRIPTION
-----------

Description ripped from murder's page:

Murder is a method of using Bittorrent to distribute files to a large amount
of servers within a production environment. This allows for scaleable and fast
deploys in environments of hundreds to tens of thousands of servers where
centralized distribution systems wouldn't otherwise function. A "Murder" is
normally used to refer to a flock of crows, which in this case applies to a
bunch of servers doing something.

For an intro video, see:
[Twitter - Murder Bittorrent Deploy System](http://vimeo.com/11280885)


USAGE
-----------

Deploys a build to a small cluster consisting of a master node and 3 workers.

	import pymurder

	master = 'master1'
	workers = ['worker1', 'worker2', 'worker3']

	pym = pymurder.PyMurder({
		    'tracker': [master],
		    'seeder': [master],
		    'peer': workers + [master],
		    'remote_murder_path': '/opt/local/murder',
		    'pymurder_home': '.',
		    'user': 'ubuntu',
		    'key_filename': ~/.ssh/ec2key.pem
	})

        pym.distribute_files()
        pym.start_tracker()
        pym.create_torrent('pyhoard', '/opt/local/murder')

	sendFiles() # Send the build to the master server 

        pym.start_seeding('pyhoard')
        pym.start_peering('pyhoard', '/opt/local/murder')
        pym.stop_all_peering()
        pym.stop_seeding('pyhoard')
        pym.stop_tracker()

	def sendFiles(master):
		""" Rsyncs the pyhoard files to the master for creation of the torrent
		to be used to deploy to all peers
		"""

		master = ec2.getRunningMasterPublicDns()
			    
		callSpec = ['/usr/bin/rsync', "-avz", "--delete", "-e",
			"ssh -i ~/.ssh/ec2key.pem -oStrictHostKeyChecking=no",
			"~/build1/",
			"%s@%s:%s" % ('ubuntu', master,\
			    '~')]

		proc = subprocess.Popen(callSpec)
		proc.wait()


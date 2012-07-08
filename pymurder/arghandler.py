import os

class ArgHandler:
    def __init__(self, args):
        self.args = args
        pass

    def getHosts(self, *roles):
        hosts = []

        for role in roles:
            hosts += self.args[role]

        # De-dupe
        seen = set()
        seen_add = seen.add
        return [ x for x in hosts if x not in seen and not seen_add(x)]

    def remoteMurderPath(self):
        return self.args['remote_murder_path']

    def distPath(self):
        return os.path.abspath(os.path.join(self.args['pymurder_home'], 'dist'))

    def trackerPort(self):
        port = 8998
        if 'tracker_port' in self.args:
            port = int(self.args['tracker_port'])

        return port

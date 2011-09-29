#!bin/python
import web, pymongo, random, json, datetime
from dateutil.tz import tzutc
from web.contrib.template import render_genshi
render = render_genshi(['.'], auto_reload=True)

alphabet = 'abcdefghijklmnpqrstuvwxyz123456789'
db = pymongo.Connection('localhost', 27017, tz_aware=True)['shortener']
uris = db['uris']
follows = db['follows']

class index(object):
    def GET(self):
        web.header("content-type", "application/json")
        return render.index()

def newShort():
    for tries in range(500):
        size = 3 + tries / 50
        s = ''.join(random.choice(alphabet) for i in range(size))
        if not uris.find_one({"short" : s}):
            return s
    raise ValueError("failed to find a new short URI code")

class shortLink(object):
    def GET(self):
        longUri = web.input()['long']
        # still full of races, including multiple shorts for one long
        # (ok) and multiple longs getting one short (bad)
        match = uris.find_one({"long" : longUri})
        if not match:
            match = {"long" : longUri, "short" : newShort()}
            uris.insert(match)
            
        del match['_id']

        web.header("content-type", "application/json")
        return json.dumps(match)

class shortLinkTest(object):
    def GET(self):
        match = uris.find_one({"long" : web.input()['long']})
        if not match:
            raise web.NotFound()
        del match['_id']
        web.header("content-type", "application/json")
        return json.dumps(match)

class follow(object):
    def GET(self, short):
        match = uris.find_one({"short" : short})
        if not match:
            raise web.NotFound()
        del match['_id']
        match['t'] = datetime.datetime.now(tzutc())
        follows.insert(match)
        raise web.SeeOther(match["long"])

app = web.application((r"/", "index",
                       r"/shortLink", "shortLink",
                       r"/shortLinkTest", "shortLinkTest",
                       r"/follow/(.*)", "follow",
                       ), globals())
if __name__ == '__main__':
    app.run()

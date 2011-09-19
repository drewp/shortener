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

class shortLink(object):
    def GET(self):
        longUri = web.input()['long']
        # still full of races, but they mostly end up with multiple
        # shorts for one long, which isn't bad
        match = uris.find_one({"long" : longUri})
        if not match:
            for tries in range(500):
                size = 3 + tries / 50
                newShort = ''.join(random.choice(alphabet) for i in range(size))
                if not uris.find_one({"short" : newShort}):
                    break

            match = {"long" : longUri, "short" : newShort}
            uris.insert(match)
            
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
                       r"/follow/(.*)", "follow",
                       ), globals())
if __name__ == '__main__':
    app.run()

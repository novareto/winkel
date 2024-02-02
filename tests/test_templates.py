from winkel.templates import Templates


templates = Templates("./templates")
templates['views/index']


templates1 = Templates("./templates/form")
templates2 = Templates("./templates/views")
templates3 = templates1 | templates2
assert list(templates3.keys()) == ['other', 'something', 'index']
assert templates3.cache == {}


templates1 = Templates("./templates/form")
templates1['other']
templates2 = Templates("./templates/views")
templates2['index']
templates3 = templates1 | templates2
assert list(templates3.keys()) == ['other', 'something', 'index']
assert list(templates3.cache.keys()) == ['other', 'index']

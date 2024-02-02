from winkel.components import Contents
from winkel.prototypes import User, Preferences, UserProxy


contents1 = Contents()
contents1.create(User, 'user', workflow=1, proxy=UserProxy)

contents2 = Contents()
contents2.create(Preferences, 'preferences')

contents = contents1 | contents2
print(contents)
print(contents['user'])

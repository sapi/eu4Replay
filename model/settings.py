
from datetime import datetime
import json
import os

from namespaces import Namespace

# The parsing here takes place at module level.
#
# This has two advantages:
#  (1) it lets us throw an exception as early as possible, ie at import; and
#  (2) other classes can treat the module itself as a quasi-singleton.
#
# Unfortunately, it does make the code rather ugly.
# We could improve it somewhat by using DEFINES in place of string constants,
# but that's a task for another day.

# First, we load the settings file (which is hard-coded)
with open('settings.cfg', 'rU') as _f:
    _d = json.loads(_f.read())

# Second, we check for the validity of settings
class InvalidSettings(Exception):
    pass

# all values need to be there
_expectedValues = (
        'eu4_directory',
        'start_date',
        'end_date',
        'month_names',
    )

_missingValues = [_v for _v in _expectedValues if _v not in _d]

if _missingValues:
    raise InvalidSettings('Missing values in settings file: %s'%(
        ', '.join(_missingValues)))

# the eu4 directory needs to actually be a directory
if not os.path.isdir(_d['eu4_directory']):
    raise InvalidSettings('Invalid EU4 Directory: %s'%_d['eu4_directory'])

# the dates need to be parseable
try:
    _d['start_date'] = datetime(*map(int, _d['start_date'].split('.')))
    _d['end_date'] = datetime(*map(int, _d['end_date'].split('.')))
except:
    raise InvalidSettings('Invalid date range: %s - %s'%(
        _d['start_date'], _d['end_date']))

if _d['start_date'] >= _d['end_date']:
    raise InvalidSettings('Invalid date range: %s - %s'%(
        _d['start_date'], _d['end_date']))

# all month names must be provided
if len(_d['month_names']) != 12:
    raise InvalidSettings('Wrong number of month names')

# convert gif_settings to a Namespace
_d['gif_settings'] = Namespace(**_d['gif_settings'])

# Now, we import the settings to module scope
globals().update(_d)

# Finally, we must delete everything in globals() which isn't a setting
for _v in [_v for _v in globals() if _v not in _d]:
    del globals()[_v]

del globals()['_v']

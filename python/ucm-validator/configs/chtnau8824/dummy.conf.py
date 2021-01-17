#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "chtnau8824/chtnau8824.conf@HiFi.conf: 'If'.'Controls'.'Condition' - False": 1,
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}

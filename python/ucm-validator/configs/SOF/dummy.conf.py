#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'If'.'0'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'If'.'0'.'True'.'If'.'mono'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'If'.'0'.'True'.'If'.'dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'If'.'0'.'True'.'If'.'in3'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5650'.'True'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'If'.'0'.'True'.'If'.'headphones'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'If'.'0'.'True'.'If'.'dmic'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'If'.'0'.'True'.'If'.'in12'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_max98090'.'True'.'SectionVerb'.'If'.'platform'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_max98090'.'True'.'SectionVerb'.'If'.'Quawks'.'Condition' - True": 1,
  "cht-bsw-rt5672/cht-bsw-rt5672-stereo-dmic2.conf@HiFi-stereo-dmic2.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "cht-bsw-rt5672/cht-bsw-rt5672.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "bytcht-es8316/bytcht-es8316.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtnau8824/chtnau8824.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtnau8824/chtnau8824-mono.conf@HiFi-mono.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "bytcr-rt5651/bytcr-rt5651.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "bytcht-cx2072x/bytcht-cx2072x.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtrt5645/chtrt5645.conf@HiFi.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtrt5645/chtrt5645-dmic1.conf@HiFi-dmic1.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtrt5645/chtrt5645-dmic2.conf@HiFi-dmic2.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
  "chtrt5645/chtrt5645-mono-speaker-analog-mic.conf@HiFi-mono-speaker-analog-mic.conf: 'SectionVerb'.'If'.'Controls'.'Condition' - False": 1,
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}

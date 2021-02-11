#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_cx2072x'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_max98090'.'True'.'Include'.'main'.'SectionVerb'.'If'.'platform'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_max98090'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Quawks'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'Include'.'main'.'If'.'0'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'mono'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_es8316'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'in1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_nau8824'.'True'.'Include'.'main'.'SectionVerb'.'If'.'SST'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_nau8824'.'True'.'Include'.'main'.'If'.'cfg-mspk'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_nau8824'.'True'.'Include'.'main'.'If'.'cfg-mic'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'in3'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'If'.'cfg-dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'If'.'cfg-dmic2'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'If'.'cfg-mspk'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'If'.'dmic'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5645'.'True'.'Include'.'main'.'SectionDevice'.'Speaker'.'If'.'mspk'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'Include'.'main'.'If'.'0'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5640'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'mono'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5650'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'Condition' - False": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'mono'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'headphones'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'dmic'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'in2'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5651'.'True'.'Include'.'main'.'If'.'0'.'True'.'Include'.'comp'.'If'.'in12'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'SectionVerb'.'If'.'Controls'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'cfg-dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'cfg-dmic2'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'mspk'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'dmic1'.'False'.'If'.'dmic2'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'dmic2'.'False'.'If'.'dmic1'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_rt5672'.'True'.'Include'.'main'.'If'.'dmic2'.'Condition' - True": 1,
  "SOF/SOF.conf@HiFi.conf: 'If'.'bytcht_wm5102'.'Condition' - True": 1,
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}

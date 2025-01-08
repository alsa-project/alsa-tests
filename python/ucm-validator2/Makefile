DBGCMD?=
V?=0
ALSA_UCM_DIR?=../../../alsa-ucm-conf/ucm2

all: configs
	@exit 0

.PHONY: configs
configs:
	$(DBGCMD) ./ucm.py configs --level=$(V) --ucmdir=$(ALSA_UCM_DIR)

DBGCMD?=
LOGLEVEL?=0
ALSA_UCM_DIR?=../../../alsa-ucm-conf/ucm2

all: verify configs
	@exit 0

.PHONY: verify
verify:
	./ucm.py --level $(LOGLEVEL) all $(ALSA_UCM_DIR)

.PHONY: configs
configs:
	$(DBGCMD) ./ucm.py --level $(LOGLEVEL) configs $(ALSA_UCM_DIR) configs

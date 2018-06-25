

NCS_IPC_PORT=$(shell xmllint --xpath \
"//*[local-name()='ncs-ipc-address']/*[local-name()='port']/text()" ncs.conf)


ifeq ($(NCS_IPC_PORT),)
$(error "Could not find ncs ipc port. Is xmllint installed?")
endif

all:

start app-start:
	NCS_IPC_PORT=$(NCS_IPC_PORT)   \
	  sname=$(NCS_NAME) ncs --with-package-reload  \
           --ignore-initial-validation $(NCS_FLAGS)
	NCS_IPC_PORT=$(NCS_IPC_PORT)  ../init.sh

stop app-stop:
	@NCS_IPC_PORT=$(NCS_IPC_PORT) ncs --stop >/dev/null 2>&1; true

cli:
	NCS_IPC_PORT=$(NCS_IPC_PORT) ncs_cli -u admin

cli-j: cli
cli-c:
	NCS_IPC_PORT=$(NCS_IPC_PORT) ncs_cli -C -u admin

status:
	@NCS_IPC_PORT=$(NCS_IPC_PORT) ncs --status > /dev/null 2>&1; \
	if [ $$? = 0 ]; then echo "$(NCS_NAME): UP"; \
            else echo "$(NCS_NAME): ERR"; fi

clean reset: stop
	@rm -rf state/* ncs-cdb/* logs/*


.PHONY: all init start stop cli status reset clean

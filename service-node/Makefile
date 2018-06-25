NCS_NAME=nso-srv
all:

start app-start:
	sname=$(NCS_NAME) ncs --with-package-reload  \
           --ignore-initial-validation $(NCS_FLAGS)
	./init.sh

stop app-stop:
	ncs --stop >/dev/null 2>&1; true

cli:
	ncs_cli -u admin

cli-j: cli
cli-c:
	ncs_cli -C -u admin

status:
	@ncs --status > /dev/null 2>&1; \
	if [ $$? = 0 ]; then echo "$(NCS_NAME): UP"; \
            else echo "$(NCS_NAME): ERR"; fi

clean reset: stop
	@rm -rf state/* ncs-cdb/* logs/*

.PHONY: all init start stop cli status reset clean

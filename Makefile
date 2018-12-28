
all:
	@echo "Use 'make install' to install tesladata on this system"

install:
	@test -e /usr/local/tesladata || mkdir /usr/local/tesladata
	@cp src/poller.py /usr/local/tesladata/poller.py
	@cp config.yaml /usr/local/tesladata/config.yaml
	@cp systemd/tesladata-poller.service /etc/systemd/system/tesladata-poller.service

	@chmod 750 /usr/local/tesladata/poller.py
	@chmod 640 /usr/local/tesladata/config.yaml
	@chmod 644 /etc/systemd/system/tesladata-poller.service

	@systemctl daemon-reload
	@systemctl enable tesladata-poller.service
	@echo "Tesladata is installed and enabled as a systemd service"
	@echo "Start polling the Tesla with the command 'systemctl start tesladata-poller.service'"

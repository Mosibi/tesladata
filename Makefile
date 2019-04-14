
all:
	@echo "Use 'make install' to install tesladata on this system"

install:
	@test -e /usr/local/tesladata || mkdir /usr/local/tesladata
	@cp src/poller.py /usr/local/tesladata/poller.py
	@cp src/tesladata.py /usr/local/tesladata/tesladata.py
	@cp src/teslajson.py /usr/local/tesladata/teslajson.py
	@cp src/mongo-to-influxdb.py /usr/local/tesladata/mongo-to-influxdb.py
	@cp src/mongo-watcher.py /usr/local/tesladata/mongo-watcher.py
	@cp src/endpoints.py /usr/local/tesladata/endpoints.py
	@cp src/sleepy-to-sleeping.py /usr/local/tesladata/sleepy-to-sleeping.py

	@test -e /usr/local/tesladata/config.yaml || cp config.yaml /usr/local/tesladata/config.yaml

	@cp systemd/tesladata-poller.service /etc/systemd/system/tesladata-poller.service
	@cp systemd/tesladata-watcher.service /etc/systemd/system/tesladata-watcher.service

	@chmod 750 /usr/local/tesladata/poller.py
	@chmod 750 /usr/local/tesladata/tesladata.py
	@chmod 750 /usr/local/tesladata/mongo-watcher.py
	@chmod 750 /usr/local/tesladata/endpoints.py
	@chmod 750 /usr/local/tesladata/sleepy-to-sleeping.py
	@chmod 750 /usr/local/tesladata/mongo-to-influxdb.py
	@chmod 640 /usr/local/tesladata/config.yaml
	@chmod 644 /etc/systemd/system/tesladata-poller.service
	@chmod 644 /etc/systemd/system/tesladata-watcher.service

	@systemctl daemon-reload
	@systemctl enable tesladata-poller.service
	@systemctl enable tesladata-watcher.service
	@echo "Tesladata services 'poller' and 'watcher' are installed and enabled as a systemd service"
	@echo "Start polling the Tesla with the command 'systemctl start tesladata-poller.service'"
	@echo "Start the MongoDB watcher with the command 'systemctl start tesladata-watcher.service'"

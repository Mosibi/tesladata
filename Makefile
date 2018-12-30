
all:
	@echo "Use 'make install' to install tesladata on this system"

install:
	@test -e /usr/local/tesladata || mkdir /usr/local/tesladata
	@cp src/poller.py /usr/local/tesladata/poller.py
	@cp src/tesladata.py /usr/local/tesladata/tesladata.py
	@cp src/mongo2influxdb.py /usr/local/tesladata/mongo2influxdb.py
	@cp config.yaml /usr/local/tesladata/config.yaml
	@cp systemd/tesladata-poller.service /etc/systemd/system/tesladata-poller.service
	@cp systemd/tesladata-mongo2influxdb.service /etc/systemd/system/tesladata-mongo2influxdb.service
	@cp systemd/tesladata-mongo2influxdb.timer /etc/systemd/system/tesladata-mongo2influxdb.timer

	@chmod 750 /usr/local/tesladata/poller.py
	@chmod 750 /usr/local/tesladata/tesladata.py
	@chmod 750 /usr/local/tesladata/mongo2influxdb.py
	@chmod 640 /usr/local/tesladata/config.yaml
	@chmod 644 /etc/systemd/system/tesladata-poller.service
	@chmod 644 /etc/systemd/system/tesladata-mongo2influxdb.service
	@chmod 644 /etc/systemd/system/tesladata-mongo2influxdb.timer

	@systemctl daemon-reload
	@systemctl enable tesladata-poller.service
	@echo "Tesladata is installed and enabled as a systemd service"
	@echo "Start polling the Tesla with the command 'systemctl start tesladata-poller.service'"
	@echo "Start mongo2influxdb with the command 'systemctl start tesladata-mongo2influxdb.service', this timer starts the service tesladata-mongo2influxdb.service"
	@echo "every minute to read data from MongoDB and inject it in InluxDB. This timer can be shown with 'systemctl list-timers'"

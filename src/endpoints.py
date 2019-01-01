import tesladata


def vehicle_state(server, data):
    tesladata.influx_write(
        servername=server,
        measurement="vehicle_state",
        entity="odometer",
        vin=data["vin"],
        value=data["odometer"],
        ms=data["timestamp"],
    )


def vehicle(server, data):
    sleeping = 0

    if data["state"] == "asleep":
        sleeping = 1

    tesladata.influx_write(
        servername=server,
        measurement="vehicle_state",
        entity="sleeping",
        vin=data["vin"],
        value=sleeping,
        ms=data["timestamp"],
    )


def custom_data(server, data):
    try:
        if data["sleepy"] is True:
            tesladata.influx_write(
                servername=server,
                measurement="custom_data",
                entity="sleepy",
                vin=data["vin"],
                value=1,
                ms=data["timestamp"],
            )
    except KeyError:
        pass


def charge_state(server, data):
    tesladata.influx_write(
        servername=server,
        measurement="charge_state",
        entity="battery_level",
        vin=data["vin"],
        value=data["battery_level"],
        ms=data["timestamp"],
    )

    tesladata.influx_write(
        servername=server,
        measurement="charge_state",
        entity="ideal_battery_range",
        vin=data["vin"],
        value=float(data["ideal_battery_range"] * 1.609344),
        ms=data["timestamp"],
    )

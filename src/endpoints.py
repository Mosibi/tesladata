import tesladata


def vehicle_config(server, data):
    pass


def climate_state(server, data):
    pass


def drive_state(server, data):
    pass


def gui_settings(server, data):
    pass


def mobile_enabled(server, data):
    pass


def nearby_charging_sites(server, data):
    pass


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
    tesladata.influx_write(
        servername=server,
        measurement="vehicle_state_txt",
        entity="state",
        vin=data["vin"],
        value=data["state"],
        ms=data["timestamp"],
    )


def custom_data(server, data):
    if 'sleepy' in data:
        if data["sleepy"] is True:
            tesladata.influx_write(
                servername=server,
                measurement="custom_data",
                entity="sleepy",
                vin=data["vin"],
                value=1,
                ms=data["timestamp"],
            )
    
    if 'est_ideal_maxrange' in data:
        tesladata.influx_write(
            servername=server,
            measurement="custom_data",
            entity="est_ideal_maxrange",
            vin=data["vin"],
            value=data["est_ideal_maxrange"],
            ms=data["timestamp"],
        )
    

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

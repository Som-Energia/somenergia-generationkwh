from marshmallow import Schema, fields, pre_load, post_load


class MeasurementSchema(Schema):    
    name = fields.String(position=0, required=True)
    create_at = fields.DateTime(position=1, format='%Y-%m-%d %H:%M', required=True)
    datetime = fields.DateTime(position=2, format='%Y-%m-%d %H:%M', required=True)
    ae = fields.Integer(position=3)

    @pre_load
    def pre_measurement(self, data):
        import datetime
        if isinstance(data['datetime'], datetime.datetime):
            data['datetime'] = data['datetime'].strftime('%Y-%m-%d %H:%M')
        if isinstance(data['create_at'], datetime.datetime):
            data['create_at'] = data['create_at'].strftime('%Y-%m-%d %H:%M')
        data.pop('_id', None)
        return data

    @post_load
    def post_measurement(self, data):
        from plantmeter.resource import Measurement
        data.pop('create_at', None)
        return Measurement(**data)


class MeterSchema(Schema):
    name = fields.String(position=0, required=True)
    description = fields.String(position=1, required=True)
    enabled = fields.Boolean(position=2, required=True)
    uri = fields.String(position=1, required=True)

    @post_load
    def post_meter(self, data):
        from plantmeter.resource import Meter 
        return Meter(**data)


class PlantSchema(Schema):
    name = fields.String(position=0, required=True)
    description = fields.String(position=1, required=True)
    enabled = fields.Boolean(position=2, required=True)
    meters = fields.Nested(MeterSchema, position=3, many=True, required=True)

    @post_load
    def post_plant(self, data):
        from plantmeter.resource import Plant 
        return Plant(**data)


class VirtualPlantSchema(Schema):
    name = fields.String(position=0, required=True)
    description = fields.String(position=1, required=True)
    enabled = fields.Boolean(position=2, required=True)
    plants = fields.Nested(PlantSchema, position=3, many=True, required=True)

    @post_load
    def post_vplant(self, data):
        from plantmeter.resource import VirtualPlant
        return VirtualPlant(**data)

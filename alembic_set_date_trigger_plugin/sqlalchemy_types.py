from sqlalchemy import DateTime


class TriggerOnEnum(str):
    update = "update"
    insert = "insert"


def DateTimeWithSetDateTrigger(trigger_on: TriggerOnEnum, datetime_processor=DateTime, *args, **kwargs):
    """SQLAlchemy Datetime type with support for the creation of a Postgresql trigger to update the date"""

    class DateTimeWithSetDateTriggerClass(datetime_processor):
        def __init__(self, trigger_on: TriggerOnEnum, *args, **kwargs):
            self.trigger_on = trigger_on
            super().__init__(*args, **kwargs)

    return DateTimeWithSetDateTriggerClass(trigger_on=trigger_on, *args, **kwargs)

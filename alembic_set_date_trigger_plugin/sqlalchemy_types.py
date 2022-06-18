from sqlalchemy import DateTime


class TriggerOnEnum(str):
    update = "update"
    insert = "insert"


class DateTimeWithSetDateTrigger(DateTime):
    """SQLAlchemy Datetime type with support for the creation of a Postgresql trigger to update the date"""

    def __init__(self, trigger_on: TriggerOnEnum, *args, **kwargs):
        self.trigger_on = trigger_on
        super().__init__(*args, **kwargs)

# Alembic Set Date Trigger Plugin

<p>
    <a href="https://github.com/samarcan/alembic-set-date-trigger-plugin/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/markdown-subtemplate.svg" alt="License" height="18"></a>
    <a href="https://badge.fury.io/py/alembic-set-date-trigger-plugin"><img src="https://badge.fury.io/py/alembic-set-date-trigger-plugin.svg" alt="PyPI version" height="18"></a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Codestyle Black" height="18">
    </a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python version" height="18"></a>
    <a href=""><img src="https://img.shields.io/badge/postgresql-11+-blue.svg" alt="PostgreSQL version" height="18"></a>
</p>

---

## Description

`Alembic set date trigger plugin` is a plugin for Alembic that adds support for automatic update DateTime fields with
PostgreSQL triggers and functions, allowing to keep track of the triggers and function creation through alembic
migrations and auto-detecting them from your SQLAlchemy tables definition.

## Installation

```shell
pip install alembic-set-date-trigger-plugin
```

## How to use

Import the plugin into your alembic `env.py` file:

```python
#  env.py

import alembic_set_date_trigger_plugin as asdtp
```

This library implement a new type of column for SQLAlchemy based in the SQLAlchemy `Datetime` type. The functionality is
the same, but it adds a `trigger_on` fields to indicate when the trigger should be activated, there are two options:
`update` and `create`.

Additionally the base class from which DateTimeWithSetDateTrigger will inherit can be defined through the
`datetime_processor` parameter, the default value is the SqlAlchemy Datetime type.

In your SQLAlchemy tables definition you can add the new type `DateTimeWithSetDateTrigger`.

```python
from alembic_set_date_trigger_plugin.sqlalchemy_types import DateTimeWithSetDateTrigger, TriggerOnEnum

my_table = Table(
    "my_table",
...
    #  Without defining datetime_processor
    Column("updated_at", DateTimeWithSetDateTrigger(trigger_on=TriggerOnEnum.update)),
    Column("created_at", DateTimeWithSetDateTrigger(trigger_on=TriggerOnEnum.insert)),
    Column("created_at", DateTimeWithSetDateTrigger(trigger_on=(TriggerOnEnum.insert, TriggerOnEnum.update))),
    
    #  Defining datetime_processor
    Column("updated_at", DateTimeWithSetDateTrigger(trigger_on=TriggerOnEnum.update, datetime_processor=ArrowType)),
...
)
```

You can also change the default PostgreSQL function for setting the current datetime. Take into account that the name 
of the column that need to be updated is passed to the function and can be obtained with `TG_ARGV[0]`

```postgresql
-- Default function

CREATE OR REPLACE FUNCTION asdtp_set_date()
RETURNS TRIGGER AS $$
   BEGIN
     NEW := json_populate_record(NEW, json_build_object(TG_ARGV[0], now()));
     RETURN NEW;
 END;
$$ LANGUAGE plpgsql;
```

```python
#  env.py

import alembic_set_date_trigger_plugin as asdtp

asdtp.modify_set_date_function("""
BEGIN
    <CUSTOM LOGIC>
END;
""")
```

When you run the alembic autogenerate migration command it will detect the changes and will generate a migration file
like this:

```python
"""Create trigger and function

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "<revision_id>"
down_revision = "<down_revision_id>"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_set_date_function()
    op.create_set_date_trigger(
        "my_table", "updated_at", "update", "my_table__updated_at__on_update__set_date_trigger"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_set_date_trigger(
        "my_table", "updated_at", "update", "my_table__updated_at__on_update__set_date_trigger"
    )
    op.drop_set_date_function()
    # ### end Alembic commands ###
```

* `op.create_set_date_function`: This operation will create a PostgreSQL function that will be called by the triggers,
   it is on charge of updating the specified datetime column to `now()`. It is created only the first time we create a
   trigger.
* `op.create_set_date_trigger`: This operation will create a PostgreSQL trigger for the specified datetime column.

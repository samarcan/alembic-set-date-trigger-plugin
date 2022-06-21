from alembic.autogenerate import comparators, renderers
from alembic.operations import MigrateOperation, Operations

from alembic_set_date_trigger_plugin.function_op import (
    FUNCTION_NAME,
    CreateSetDateFunctionOp,
    date_function_exists_in_db,
)


@Operations.register_operation("create_set_date_trigger")
class CreateSetDateTriggerOp(MigrateOperation):
    def __init__(self, table_name, column_name, trigger_on, trigger_name):
        self.trigger_name = trigger_name
        self.column_name = column_name
        self.trigger_on = trigger_on
        self.table_name = table_name

    @classmethod
    def create_set_date_trigger(cls, operations, table_name, column_name, trigger_on, trigger_name, **kw):
        op = CreateSetDateTriggerOp(table_name, column_name, trigger_on, trigger_name, **kw)
        return operations.invoke(op)

    def reverse(self):
        return DropSetDateTriggerOp(self.table_name, self.column_name, self.trigger_on, self.trigger_name)


@Operations.register_operation("drop_set_date_trigger")
class DropSetDateTriggerOp(MigrateOperation):
    def __init__(self, table_name, column_name, trigger_on, trigger_name):
        self.trigger_name = trigger_name
        self.column_name = column_name
        self.trigger_on = trigger_on
        self.table_name = table_name

    @classmethod
    def drop_set_date_trigger(cls, operations, table_name, column_name, trigger_on, trigger_name, **kw):

        op = DropSetDateTriggerOp(table_name, column_name, trigger_on, trigger_name, **kw)
        return operations.invoke(op)

    def reverse(self):
        return CreateSetDateTriggerOp(self.table_name, self.column_name, self.trigger_on, self.trigger_name)


@Operations.implementation_for(CreateSetDateTriggerOp)
def create_set_date_trigger(operations, operation):
    operations.execute(
        f"""
        CREATE TRIGGER {operation.trigger_name} BEFORE {operation.trigger_on} ON {operation.table_name}
        FOR EACH ROW EXECUTE PROCEDURE {FUNCTION_NAME}('{operation.column_name}')
        """
    )


@Operations.implementation_for(DropSetDateTriggerOp)
def drop_set_date_trigger(operations, operation):
    operations.execute(f"DROP TRIGGER IF EXISTS {operation.trigger_name} ON {operation.table_name}")


@renderers.dispatch_for(CreateSetDateTriggerOp)
def render_create_sequence(autogen_context, op):
    return f'op.create_set_date_trigger("{op.table_name}", "{op.column_name}", "{op.trigger_on}", "{op.trigger_name}")'


@renderers.dispatch_for(DropSetDateTriggerOp)
def render_drop_sequence(autogen_context, op):
    return f'op.drop_set_date_trigger("{op.table_name}", "{op.column_name}", "{op.trigger_on}", "{op.trigger_name}")'


@comparators.dispatch_for("schema")
def compare_set_date_triggers(autogen_context, upgrade_ops, schemas):
    db_set_date_triggers = _get_db_set_date_triggers(autogen_context, schemas)
    sqlalchemy_set_date_triggers = _get_sqlalchemy_models_set_date_triggers(autogen_context)

    creation_ops = sqlalchemy_set_date_triggers.difference(db_set_date_triggers)
    if creation_ops and not date_function_exists_in_db(autogen_context, schemas):
        from alembic_set_date_trigger_plugin.function_op import (
            SET_DATE_FUNCTION,
        )  # pylint: disable=import-outside-toplevel

        upgrade_ops.ops.append(CreateSetDateFunctionOp(new_function=SET_DATE_FUNCTION))

    for table_name, column_name, trigger_on, trigger_name in creation_ops:
        upgrade_ops.ops.append(CreateSetDateTriggerOp(table_name, column_name, trigger_on, trigger_name))

    for (
        table_name,
        column_name,
        trigger_on,
        trigger_name,
    ) in db_set_date_triggers.difference(sqlalchemy_set_date_triggers):
        upgrade_ops.ops.append(DropSetDateTriggerOp(table_name, column_name, trigger_on, trigger_name))


def _get_db_set_date_triggers(autogen_context, schemas):
    db_set_date_triggers = set()
    for sch in schemas:
        sch = autogen_context.dialect.default_schema_name if sch is None else sch
        for row in autogen_context.connection.execute(
            "SELECT trigger_name FROM information_schema.triggers;",
            nspname=sch,
        ):
            trigger_name = row[0]
            if trigger_name.endswith("__set_date_trigger"):
                table_name = trigger_name.replace("__set_date_trigger", "").split("__")[0]
                column_name = trigger_name.replace("__set_date_trigger", "").split("__")[1]
                trigger_on = trigger_name.replace("__set_date_trigger", "").split("__")[2].replace("on_", "")
                db_set_date_triggers.add((table_name, column_name, trigger_on, trigger_name))
    return db_set_date_triggers


def _get_sqlalchemy_models_set_date_triggers(autogen_context):
    sqlalchemy_set_date_triggers = set()
    tables = autogen_context.metadata.tables
    for table_name in autogen_context.metadata.tables:
        columns = tables[table_name].columns
        target_columns = [
            (column_name, columns[column_name])
            for column_name in columns.keys()
            if type(columns[column_name].type).__name__ == "DateTimeWithSetDateTriggerClass"
        ]
        for column_name, column in target_columns:
            trigger_on = column.type.trigger_on
            sqlalchemy_set_date_triggers.add(
                (
                    table_name,
                    column_name,
                    trigger_on,
                    f"{table_name}__{column_name}__on_{trigger_on}__set_date_trigger",
                )
            )
    return sqlalchemy_set_date_triggers

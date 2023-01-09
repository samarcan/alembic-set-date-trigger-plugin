from alembic.autogenerate import renderers, comparators
from alembic.operations import MigrateOperation, Operations

FUNCTION_NAME = "asdtp_set_date"
DEFAULT_SET_DATE_FUNCTION = SET_DATE_FUNCTION = """
    BEGIN
        NEW := json_populate_record(NEW, json_build_object(TG_ARGV[0], now()));
        RETURN NEW;
    END;
"""


def modify_set_date_function(new_function):
    global SET_DATE_FUNCTION
    SET_DATE_FUNCTION = new_function


@Operations.register_operation("create_set_date_function")
class CreateSetDateFunctionOp(MigrateOperation):
    def __init__(self, already_exists=False, new_function=None, old_function=None):
        self.already_exists = already_exists
        self.new_function = new_function or DEFAULT_SET_DATE_FUNCTION
        self.old_function = old_function

    @classmethod
    def create_set_date_function(
        cls,
        operations,
        new_function=None,
        already_exists=False,
        old_function=None,
        **kw,
    ):
        op = CreateSetDateFunctionOp(already_exists, new_function, old_function, **kw)
        return operations.invoke(op)

    def reverse(self):
        if self.already_exists:
            return CreateSetDateFunctionOp(new_function=self.old_function)
        return DropSetDateFunctionOp()


@Operations.register_operation("drop_set_date_function")
class DropSetDateFunctionOp(MigrateOperation):
    @classmethod
    def drop_set_date_function(cls, operations, **kw):

        op = DropSetDateFunctionOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        return CreateSetDateFunctionOp()


@Operations.implementation_for(CreateSetDateFunctionOp)
def create_set_date_function(operations, operation):
    operations.execute(
        f"""
        CREATE OR REPLACE FUNCTION {FUNCTION_NAME}()
        RETURNS TRIGGER AS $$
            {operation.new_function}
        $$ LANGUAGE plpgsql;
        """
    )


@Operations.implementation_for(DropSetDateFunctionOp)
def drop_set_date_function(operations, operation):
    operations.execute(f"DROP FUNCTION IF EXISTS {FUNCTION_NAME}")


@renderers.dispatch_for(CreateSetDateFunctionOp)
def render_create_sequence(autogen_context, op):
    if _format_fcn_for_comparison(op.new_function) == _format_fcn_for_comparison(DEFAULT_SET_DATE_FUNCTION):
        return "op.create_set_date_function()"
    return f'''op.create_set_date_function("""{op.new_function}""")'''


@renderers.dispatch_for(DropSetDateFunctionOp)
def render_drop_sequence(autogen_context, op):
    return f"op.drop_set_date_function()"


@comparators.dispatch_for("schema")
def compare_set_date_triggers(autogen_context, upgrade_ops, schemas):
    current_db_set_date_function = None
    for sch in schemas:
        sch = autogen_context.dialect.default_schema_name if sch is None else sch
        rows = list(
            autogen_context.connection.execute(
                f"select prosrc from pg_proc p where proname = '{FUNCTION_NAME}';",
                nspname=sch,
            )
        )
        if rows:
            current_db_set_date_function = rows[0][0].strip()
            break
    if not current_db_set_date_function:
        return
    if _format_fcn_for_comparison(current_db_set_date_function) != _format_fcn_for_comparison(SET_DATE_FUNCTION):
        upgrade_ops.ops.append(
            CreateSetDateFunctionOp(
                already_exists=True,
                new_function=SET_DATE_FUNCTION,
                old_function=current_db_set_date_function,
            )
        )


def date_function_exists_in_db(autogen_context, schemas):
    for sch in schemas:
        sch = autogen_context.dialect.default_schema_name if sch is None else sch
        rows = list(
            autogen_context.connection.execute(
                f"select count(*) from pg_proc p where proname = '{FUNCTION_NAME}';",
                nspname=sch,
            )
        )
        if rows[0][0] != 0:
            return True
    return False


def _format_fcn_for_comparison(fcn_str):
    return "\n".join(line.strip() for line in fcn_str.split("\n") if line.strip())

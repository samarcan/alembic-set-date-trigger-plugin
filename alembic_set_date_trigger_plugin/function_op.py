from alembic.autogenerate import renderers
from alembic.operations import MigrateOperation, Operations

FUNCTION_NAME = "asdtp_set_date"


@Operations.register_operation("create_set_date_function")
class CreateSetDateFunctionOp(MigrateOperation):
    @classmethod
    def create_set_date_function(cls, operations, **kw):
        op = CreateSetDateFunctionOp(**kw)
        return operations.invoke(op)

    def reverse(self):
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
        BEGIN
            NEW := json_populate_record(NEW, json_build_object(TG_ARGV[0], now()));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


@Operations.implementation_for(DropSetDateFunctionOp)
def drop_set_date_function(operations, operation):
    operations.execute(f"DROP FUNCTION IF EXISTS {FUNCTION_NAME}")


@renderers.dispatch_for(CreateSetDateFunctionOp)
def render_create_sequence(autogen_context, op):
    return f"op.create_set_date_function()"


@renderers.dispatch_for(DropSetDateFunctionOp)
def render_drop_sequence(autogen_context, op):
    return f"op.drop_set_date_function()"

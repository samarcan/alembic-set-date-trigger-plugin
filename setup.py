from setuptools import setup

setup(
    name="alembic_set_date_trigger_plugin",
    version="0.0.3",
    author="Samuel Martín Cantalejo",
    description="",
    license="MIT",
    url="https://github.com/samarcan/alembic-set-date-trigger-plugin",
    python_requires=">=3.6",
    install_requires=[
        "alembic>=1.5.7",
        "sqlalchemy>=1.3.0",
    ],
    packages=["alembic_set_date_trigger_plugin"],
)

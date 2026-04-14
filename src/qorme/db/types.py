import enum


class DatabaseVendor(enum.Enum):
    """Type of database vendors."""

    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MARIADB = "mariadb"
    POSTGRESQL = "postgresql"

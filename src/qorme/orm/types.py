import enum


class QueryType(enum.Enum):
    """Type of queries."""

    COUNT = "COUNT"
    EXISTS = "EXISTS"
    SELECT = "SELECT"


class RowType(enum.Enum):
    """Type of rows returned by a query."""

    DICT = "Dict"
    MODEL = "Model"
    SCALAR = "Scalar"
    SEQUENCE = "Sequence"

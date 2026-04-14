import enum


class ContextType(enum.Enum):
    """Type of contexts."""

    CLI = "CLI"
    GRAPHQL = "GraphQL"
    HTTP = "HTTP Request"
    TASK = "Task"
    TEST = "Test"
    UNDEFINED = "Undefined"

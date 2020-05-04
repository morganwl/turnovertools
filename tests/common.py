"""Common tools for tests."""

class SampleData:
    """Organizes information about test files that need to be accessed
    from the filesystem."""

    def __init__(self, name, path, description=None, inputs=None, outputs=None,
                 data=None):
        if inputs is None:
            if outputs is not None:
                inputs = list(outputs.keys())
            else:
                inputs = list()
        if outputs is None:
            outputs = dict()
        if description is None:
            description = ''
        self.name = name
        self.path = path
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.data = data

"""Parent classes for testing that subpackages conform to codebase
standards."""

class Standard2:
    """Tests to see that a subpackage meets the specifications of standard
    2, initiated in 0.0.4."""

    def test_uses_mobs_gen2(self):
        """Test that no objects from mediaobject.py and its children
        classes exist in the subpackage."""

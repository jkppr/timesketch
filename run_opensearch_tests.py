import unittest
import sys

# Attempt to import the test module by path
# This requires that the timesketch directory is in Python's search path,
# which is usually the case if the script is run from the repository root.
try:
    from timesketch.lib.datastores.opensearch_test import TestOpenSearchDataStore
except ImportError as e:
    print(f"Failed to import test module: {e}")
    print("Ensure that the script is run from the root of the Timesketch repository")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

def run_tests():
    """Discovers and runs tests from TestOpenSearchDataStore."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add tests from the specific class
    # If the class name is known and imported, this is straightforward
    suite.addTest(loader.loadTestsFromTestCase(TestOpenSearchDataStore))

    print("Running tests from timesketch.lib.datastores.opensearch_test.TestOpenSearchDataStore...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("Tests Succeeded")
        # Exiting with 0 for success, useful for scripting
        # sys.exit(0) # Let's not exit here to see output in tool
    else:
        print("Tests Failed")
        # Exiting with 1 for failure
        # sys.exit(1) # Let's not exit here to see output in tool

if __name__ == "__main__":
    run_tests()

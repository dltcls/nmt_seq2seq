import unittest

testmodules = [
    'utils.test_converter',
    'utils.test_tokenizers',
    'utils.test_utils',
    'utils.test_translator',
    'parsers.test_translation_parser',
    'parsers.test_preprocessing_parser',
    'parsers.test_training_parser'
    ]

suite = unittest.TestSuite()

for t in testmodules:
    print("Testing {}.py".format(t))
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
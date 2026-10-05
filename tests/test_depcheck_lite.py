import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import depcheck_lite as d


def write(root, path, text):
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as fh:
        fh.write(text)


class T(unittest.TestCase):
    def test_js_pkg(self):
        self.assertEqual([d.js_pkg(s) for s in ("lodash/fp", "@a/b/c", "./x", "node:fs", "react")],
                         ["lodash", "@a/b", None, None, "react"])

    def test_js(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "package.json", json.dumps({
                "dependencies": {"react": "1", "left-pad": "1", "express": "1"},
                "devDependencies": {"eslint": "1", "jest": "1", "@types/react": "1"},
                "scripts": {"lint": "eslint .", "start": "node app.js"}}))
            write(r, "src/a.js", "import React from 'react';\nconst x = require('lodash/fp');\nimport('express')")
            res = d.check_js(r)
            self.assertEqual(res["unused"], ["left-pad"])
            self.assertEqual(res["unused_dev"], ["jest"])
            self.assertEqual(res["undeclared"], ["lodash"])

    def test_python(self):
        with tempfile.TemporaryDirectory() as r:
            write(r, "requirements.txt", "requests==2.0\nPyYAML>=6\nleftover  # c\n-r other.txt\n")
            write(r, "app.py", "import os, json\nimport requests\nimport yaml\nfrom numpy import array\nimport helpers\n")
            write(r, "helpers.py", "")
            res = d.check_py(r)
            self.assertEqual(res["unused"], ["leftover"])
            self.assertEqual(res["undeclared"], ["numpy"])

    def test_requirements_parse(self):
        self.assertEqual(d.parse_requirements("Flask_SQLAlchemy>=1\n# x\n-e .\n"), {"flask-sqlalchemy"})


if __name__ == "__main__":
    unittest.main()

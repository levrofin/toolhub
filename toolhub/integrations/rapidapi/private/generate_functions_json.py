import sys
import json
import logging

log = logging.getLogger(__name__)

if len(sys.argv) < 2:
    print("Please provide a file path as a command-line argument.")
    sys.exit(1)

file_path = sys.argv[1]

_PREFIX = "data/toolenv/tools/"
_SUFFIX = "/api.py"

registry: dict = {}

with open(file_path, "r") as file:
    for line in file:
        data = json.loads(line)
        fname = data["file"]
        assert fname.startswith(_PREFIX)
        assert fname.endswith(_SUFFIX)
        namespace = fname[len(_PREFIX) : -len(_SUFFIX)].replace("/", ".")
        if namespace not in registry:
            registry[namespace] = {}
        single = data["metaVariables"]["single"]
        name = single["NAME"]["text"]
        rootUrl = json.loads(single["ROOT_URL"]["text"])
        assert single["URL_FSTRING"]["text"].startswith("f")
        urlFstring = json.loads(single["URL_FSTRING"]["text"][1:])
        qstring = (
            single["QUERYSTRING_DICT"]["text"]
            .replace("'", '"')
            .replace(":", ': "')
            .replace(",", '",')
            .replace("}", '"_DUMMY": null}')
            .replace("\t", "")
        )
        try:
            querystringDict = json.loads(qstring)
        except Exception as e:
            log.error(
                f"Error parsing querystring of {name} from {namespace}: {qstring!r}: {e}"
            )
            continue
        requiredParams = [k.strip() for k in querystringDict if k != "_DUMMY"]
        queryStringExtra = data["metaVariables"]["multi"]["QUERYSTRING_EXTRA"]
        conditionalParams: list[str] = []
        for qse in queryStringExtra:
            t = qse["text"]
            assert isinstance(t, str)
            assert t.startswith("if ")
            assert (colon := t.find(":")) > 0
            pname = t[3:colon].strip()
            assert pname.replace("_", "").isalnum(), f"Invalid name {name!r}"
            conditionalParams.append(pname)
        info = {
            "rootUrl": rootUrl,
            "urlFstring": urlFstring,
            "requiredParams": requiredParams,
            "conditionalParams": conditionalParams,
        }
        if name in registry[namespace] and registry[namespace][name] != info:
            log.error(f"Non-identical duplicate function {name} in {namespace}")
        registry[namespace][name] = info
print(json.dumps(registry))

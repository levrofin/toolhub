import os

import dynaconf
import toolhub

settings = dynaconf.Dynaconf(
    environments=True,
    settings_files=[os.path.join(os.path.dirname(toolhub.__file__), "settings.yml")],
)

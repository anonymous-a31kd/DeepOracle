# encoding=utf-8

"""
Utils for defects4j
"""

from typing import List


# D4J_PROJS = ["Chart", "Cli", "Csv", "Gson", "Lang", "Closure", "Codec", "Collections", "Compress", "JacksonCore",
            #  "JacksonDatabind", "JacksonXml", "Jsoup", "JxPath", "Math", "Mockito", "Time"]

# GBR New BUGs
# D4J_PROJS = ['AaltoXml', 'Beanutils', 'Dbcp', 'Fileupload', 'Graph', 'Mrunit', 'Pool', 'Scxml']

def parse_projects(proj: str = None) -> List[str]:
    if proj is None:
        projs = D4J_PROJS
    elif isinstance(proj, str):
        projs = proj.split(',')
    elif isinstance(proj, tuple) or isinstance(proj, list):
        projs = proj
    else:
        raise ValueError("Projects {} is unknown".format(proj))

    return projs

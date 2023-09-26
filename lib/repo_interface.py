from lib.d4j_interface import D4JRepositoryInterface
from lib.bip_interface import BIPRepositoryInterface

D4J_PROJECTS = [
    'Chart',
    'Cli',
    'Closure',
    'Codec',
    'Collections',
    'Compress',
    'Csv',
    'Gson',
    'JacksonCore',
    'JacksonDatabind',
    'JacksonXml',
    'Jsoup',
    'JxPath',
    'Lang',
    'Math',
    'Mockito',
    'Time',
]

BIP_PROJECTS = [
    'ansible',
    'cookiecutter',
    'pysnooper',
    'spacy',
    'sanic',
    'httpie',
    'keras',
    'matplotlib',
    'thefuck',
    'pandas',
    'black',
    'scrapy',
    'luigi',
    'fastapi',
    'tornado',
    'tqdm',
    'youtube-dl',
]
    

def get_repo_interface(bug_name, **ri_kwargs):
    def _name_matches_proj_list(name, proj_list):
        return any(name.lower() == proj_name.lower()
                   for proj_name in proj_list)
    proj, bug_num = bug_name.split('_')
    if _name_matches_proj_list(proj, D4J_PROJECTS):
        return D4JRepositoryInterface(bug_name, **ri_kwargs)
    elif _name_matches_proj_list(proj, BIP_PROJECTS):
        return BIPRepositoryInterface(bug_name, **ri_kwargs)
    else:
        raise ValueError(f'Unknown project {proj} detected from {bug_name}.')
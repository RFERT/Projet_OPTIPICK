from typing import Dict, Set

def normalize_dicts(dicts:list[Dict]):
    keys = set(dic.keys for dic in dicts)
    print(keys)
    temp = [set()|key for key in keys]
    print(temp)

    

if __name__ == "__main__":
    dicts = [{"restrictions": { "no_zones": ["C"], "no_fragile": True, "max_item_weight": 10 }}, {"restrictions": { "no_zones": ["C"], "no_fragile": True, "max_item_weight": 10 }}, {"restrictions": { "no_zones": ["C"], "no_fragile": True, "max_item_weight": 10 }}, {"restrictions": {}}, {"restrictions": {}}, {"restrictions": { "requires_human": True }}, {"restrictions": { "requires_human": True }}]
    normalize_dicts(dicts)
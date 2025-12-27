def deep_update(obj, key_path, value):
    # key_path is dot-separated
    keys = key_path.split('.') if isinstance(key_path, str) else key_path
    cur = obj
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value
    return obj

import os


def get_path_components(path):
    # http://stackoverflow.com/a/3167684/1103045
    dirs = []

    while 1:
        path,dr = os.path.split(path)

        if dr:
            dirs.append(dr)
        else:
            if path:
                dirs.append(path)

            break

    dirs.reverse()
    return dirs


def get_unix_path(path):
    components = get_path_components(path)

    # handle paths starting with '/'
    if components[0] == '/':
        components[0] = ''

    return '/'.join(components)

import inspect
import pathlib


def DEBUG(*args, **kwargs):
    cf = inspect.currentframe()
    cwd = pathlib.Path.cwd()
    filename = pathlib.Path(inspect.stack()[1].filename)

    print(f"{filename.relative_to(cwd)}:{cf.f_back.f_lineno}", *args, **kwargs)

import requests


def retry_on_fail(call, *args, **kwargs):
    kwargs.setdefault("max_retries", 10)
    max_retries = kwargs.pop("max_retries")

    retries = 0

    while retries < max_retries:
        try:
            return call(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print(f"connection failed: {retries}")
            retries += 1


def concat_comma(items):
    if not items:
        return

    last = items.pop() if len(items) > 1 else None
    return " and ".join([", ".join(items)] + ([last] if last else []))


def choose_items(title: str, items: list, prefix: str = None, callback: callable = None, auto_select: bool = False):
    if not items:
        print("no results")
        exit(0)
    print(title)
    for i, item in enumerate(items, 1):
        print(f" {str(i):>2}: {item}")
    while True:
        try:
            print("<<: ", end="")
            if auto_select or len(items) == 1:
                print("1")
                return None, 0
            _index = input()
            if prefix and _index.startswith(prefix):
                if value := _index.removeprefix(prefix):
                    if ret_value := callback(value):
                        return ret_value, None
            if 0 < (index := int(_index)) <= len(items):
                return None, index - 1
            continue
        except ValueError:
            pass

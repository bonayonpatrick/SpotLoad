class Chooser:
    def __init__(self, title, auto=False):
        print(f"{title}:")
        print(f"  [0] exit")

        self.auto = auto
        self.count = 1
        self.items = []

    def add_item(self, label, item):
        print(f"  [{self.count}] {label}")
        self.items.append(item)
        self.count += 1

    def choose(self):
        index = None

        if self.auto:
            if len(self.items) == 0:
                print("no items")
                return
            return self.items[0]

        if len(self.items) == 1:
            print("automatically select item 1")
            return self.items[0]

        while True:
            try:
                if (index := int(input("please select an index: "))) == 0:
                    return

                return self.items[index-1]
            except (ValueError, IndexError):
                print(f"invalid index: {index}")

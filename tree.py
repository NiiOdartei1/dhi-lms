import os

def print_tree(startpath, indent_level=0):
    for item in sorted(os.listdir(startpath)):
        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            print('│   ' * indent_level + '├── ' + item + '/')
            print_tree(path, indent_level + 1)
        else:
            print('│   ' * indent_level + '├── ' + item)

if __name__ == "__main__":
    root_dir = "."  # change to your project root if needed
    print(root_dir + "/")
    print_tree(root_dir)

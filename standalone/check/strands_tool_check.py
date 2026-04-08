import strands_tools
import inspect

print("=== strands_toolsで利用可能なモジュール ===")
for name, obj in inspect.getmembers(strands_tools):
    if inspect.ismodule(obj):
        print(f"  - {name}")

print("\n=== strands_toolsで利用可能なツール ===")
for name, obj in inspect.getmembers(strands_tools):
    if hasattr(obj, '__call__') and not name.startswith('_'):
        print(f"  - {name}")

print("\n=== strands_toolsの属性一覧 ===")
for attr in dir(strands_tools):
    if not attr.startswith('_'):
        print(f"  - {attr}")
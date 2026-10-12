#!/usr/bin/env python3
"""统一契约校验：JSON 合法性 + 契约 Schema 校验。

扫描 data/ 下 *.json 契约文件：
1. 必须是合法 JSON
2. 若存在匹配的契约 schema（仓库 docs/contract-schema 或 --schema-dir 指定目录），
   则做 jsonschema 校验
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_SCHEMA_DIR = ROOT / "docs" / "contract-schema"

TYPE_PREFIXES = ("isa", "chip", "firmware", "os")


def _find_schema(name: str, schema_dir: Path):
    if not schema_dir.exists():
        return None
    for prefix in TYPE_PREFIXES:
        if name.startswith(prefix):
            candidates = list(schema_dir.glob(f"{prefix}*schema*.json"))
            candidates += list(schema_dir.glob(f"{prefix}.schema.json"))
            for c in candidates:
                if c.exists():
                    return c
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    args = parser.parse_args()

    if not DATA_DIR.exists():
        print(f"SKIP: data dir not found: {DATA_DIR}")
        return 0

    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("SKIP: no JSON contract files under data/")
        return 0

    failed = 0
    for f in files:
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL {f.name}: invalid JSON: {e}")
            failed += 1
            continue

        schema_path = _find_schema(f.name, args.schema_dir)
        if schema_path and jsonschema is not None:
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                jsonschema.validate(obj, schema)
                print(f"OK   {f.name} (schema: {schema_path.name})")
            except jsonschema.ValidationError as e:
                print(f"FAIL {f.name}: {e.message}")
                failed += 1
            except Exception as e:
                print(f"FAIL {f.name}: schema error: {e}")
                failed += 1
        else:
            print(f"OK   {f.name} (json)")

    if failed:
        print(f"RESULT: {failed} contract(s) failed")
        return 1
    print("RESULT: all contracts valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

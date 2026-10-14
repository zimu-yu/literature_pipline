#把这次 DOI 获取流程的结果统一整理成一个 manifest.json 保存下来。
#也就是记录“我输入了什么、找到了什么、下载了什么、验证结果怎么样”。

import json
from pathlib import Path


def save_manifest(data: dict, save_path: str):
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
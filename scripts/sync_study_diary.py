#!/usr/bin/env python3
"""
学习日记同步 GitHub 脚本
用法: py scripts/sync_study_diary.py

功能:
1. 运行导航栏更新脚本
2. 提交所有更改到 Git
3. 推送到 GitHub
"""

import subprocess
import sys
from datetime import datetime

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 50)
    print("学习日记同步 GitHub")
    print("=" * 50)
    
    # 1. 更新导航栏
    print("\n[1/4] 更新导航栏...")
    code, out, err = run_cmd("py scripts/update_study_nav.py")
    if code != 0:
        print(f"[ERROR] 更新导航栏失败: {err}")
        return 1
    print(out)
    
    # 2. 添加文件
    print("[2/4] 添加文件到 Git...")
    code, out, err = run_cmd("git add -A")
    if code != 0:
        print(f"[ERROR] 添加文件失败: {err}")
        return 1
    
    # 3. 提交
    print("[3/4] 提交更改...")
    today = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"Update study diary - {today}"
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        # 可能没有更改
        if "nothing to commit" in out.lower() or "nothing to commit" in err.lower():
            print("[INFO] 没有需要提交的更改")
        else:
            print(f"[ERROR] 提交失败: {err}")
            return 1
    else:
        print(f"[OK] 已提交: {commit_msg}")
    
    # 4. 推送
    print("[4/4] 推送到 GitHub...")
    code, out, err = run_cmd("git push origin master")
    if code != 0:
        print(f"[ERROR] 推送失败: {err}")
        return 1
    print("[OK] 推送成功！")
    
    print("\n" + "=" * 50)
    print("同步完成！")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())

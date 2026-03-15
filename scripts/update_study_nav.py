#!/usr/bin/env python3
"""
学习日记导航栏自动更新脚本
- 扫描 memory 目录下的所有学习日记文件
- 生成导航链接
- 更新 README.md 或索引文件
"""

import os
import re
from datetime import datetime
from pathlib import Path

def get_study_diaries(memory_dir="memory"):
    """获取所有学习日记文件"""
    diaries = []
    pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})-study\.md$')
    
    memory_path = Path(memory_dir)
    if not memory_path.exists():
        return diaries
    
    for file in memory_path.iterdir():
        if file.is_file():
            match = pattern.match(file.name)
            if match:
                date_str = match.group(1)
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    diaries.append({
                        'date': date,
                        'date_str': date_str,
                        'filename': file.name,
                        'path': f"memory/{file.name}"
                    })
                except ValueError:
                    continue
    
    # 按日期倒序排列
    diaries.sort(key=lambda x: x['date'], reverse=True)
    return diaries

def generate_nav_section(diaries):
    """生成导航栏 Markdown"""
    lines = ["## 学习日记导航", ""]
    
    for diary in diaries:
        date_str = diary['date_str']
        display_date = diary['date'].strftime("%Y年%m月%d日")
        lines.append(f"- [{display_date}](./{diary['path']})")
    
    lines.append("")
    return "\n".join(lines)

def update_readme(nav_content, readme_path="README.md"):
    """更新 README.md 中的导航栏"""
    readme = Path(readme_path)
    
    marker_start = "<!-- STUDY_DIARY_NAV_START -->"
    marker_end = "<!-- STUDY_DIARY_NAV_END -->"
    
    new_section = f"{marker_start}\n{nav_content}{marker_end}"
    
    if readme.exists():
        content = readme.read_text(encoding='utf-8')
        
        # 检查是否已有标记
        if marker_start in content and marker_end in content:
            # 替换现有部分
            pattern = f"{marker_start}.*?{marker_end}"
            content = re.sub(pattern, new_section, content, flags=re.DOTALL)
        else:
            # 添加到文件末尾
            content = content.rstrip() + "\n\n" + new_section
        
        readme.write_text(content, encoding='utf-8')
        print(f"[OK] 已更新 {readme_path}")
    else:
        # 创建新文件
        readme.write_text(f"# 学习记录\n\n{new_section}", encoding='utf-8')
        print(f"[OK] 已创建 {readme_path}")

def main():
    print("[INFO] 扫描学习日记文件...")
    diaries = get_study_diaries()
    
    if not diaries:
        print("[WARN] 未找到学习日记文件")
        return
    
    print(f"[INFO] 找到 {len(diaries)} 篇学习日记")
    
    nav_content = generate_nav_section(diaries)
    update_readme(nav_content)
    
    print("[OK] 导航栏更新完成！")

if __name__ == "__main__":
    main()

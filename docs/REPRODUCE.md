# 复现与验证指南

推荐 Python 3.10 或更高版本，SQLite 由 Python 标准库提供。

```bash
python -m pip install -r requirements.txt
python scripts/rebuild_v11.py
python scripts/build_site.py
python tests/smoke_test.py
```

`rebuild_v11.py` 按顺序重建原题、训练导出、旧版离线浏览器、30 个错误案例及其质量报告。`build_site.py` 从规范记录重建 GitHub Pages/离线版 `index.html`。`tests/smoke_test.py` 验证 100 题、30 案例、关联和已生成网站的基本完整性。

如仅需查询，无需安装任何第三方包：

```bash
python scripts/query.py --id CAL-003
python scripts/query_error_cases.py --id EC-022
```

启动网页本地预览：

```bash
python -m http.server 8000
# 在浏览器打开 http://localhost:8000/
```

离线双击 `index.html` 也能浏览，但 MathJax 的在线公式排版可能不可用。

## 数据拆分

- `exports/train/`：70 道母题对应的训练视图。
- `exports/validation/`：15 道母题对应的验证视图。
- `exports/synthetic_test/`：15 道母题对应的合成测试视图。

**不要**直接把 `exports/` 根目录的合并输出用作训练集，这会导致合成测试内容泄漏。模拟错误案例和其对应的母题共享 `item_family_id` 与 `split`。

## 验证边界

`math_checks.py` 与 `error_case_math_checks.py` 各为项目记录执行针对性数学核验，不能代替完整人工审查。所有误区与教学策略均属于合成假设，不具有实证区分效度。

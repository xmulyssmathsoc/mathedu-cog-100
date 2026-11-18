# GitHub 发布步骤

目标账号：`xmulyssmathsoc`  
建议仓库名：`mathedu-cog-100`  
仓库简介：`Synthetic mathematics education dataset: 100 problems, 30 error cases, cognitive diagnosis & AI tutoring.`

## 1. 在目标账号创建空仓库

在 GitHub 登录 `xmulyssmathsoc`，访问 https://github.com/new ：

- Owner：`xmulyssmathsoc`
- Repository name：`mathedu-cog-100`
- Visibility：Public（若不确定可以先选 Private）
- **不要勾选自动创建 README、.gitignore 或 LICENSE**（项目中已有 README 和 .gitignore，许可由维护者另行确定）。

如果希望由 ChatGPT 的 GitHub 连接直接提交，请确保 GitHub 应用对这个新仓库授予访问和写入权限。

## 2. 通过 Git 命令发布（无需任何第三方构建）

在此项目目录执行：

```bash
git init
git branch -M main
git add .
git commit -m "feat: publish MathEdu-Cog 100 synthetic dataset v1.1"
git remote add origin https://github.com/xmulyssmathsoc/mathedu-cog-100.git
git push -u origin main
```

GitHub 根据你的身份配置可能要求浏览器登录或使用 SSH 凭据，不要把令牌写进仓库。

## 3. 启用 GitHub Pages（可选）

仓库 **Settings → Pages → Build and deployment** 选择 **Deploy from a branch**，设置 `main` 和 `/(root)`。

启用后，网站预计位于：`https://xmulyssmathsoc.github.io/mathedu-cog-100/`。**只有真正完成部署后，才能把它作为已上线网址对外公布。**

## 4. 首次公开前复核

- 确认全体维护者对题目及项目素材的发布权限。
- 决定代码与数据许可，在仓库中添加准确的 LICENSE 文件。
- 检查 README 的合成数据说明，避免把模拟案例误称真实学生记录。
- 查看 Actions 的 `Validate synthetic dataset` 是否成功运行。

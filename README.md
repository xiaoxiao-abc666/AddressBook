# Extreme Programming Assignment - Address Book

| Item | Details |
| :--- | :--- |
| **Course** | 软件工程 |
| **Members** | [832302230 薛易明 832302210 陈祺嵘 |
| **Deployment** | https://addressbook-uo5e.onrender.com |

## 1. 项目简介
这是一个基于 **Flask + Bootstrap** 开发的云端通讯录系统。我们采用了结对编程模式，实现了联系人的增删改查、Excel 导入导出以及云端部署。

## 2. 功能列表 (Features)
本项目已完成所有作业要求：
**基础功能**: 联系人的增删改查。
**收藏功能**: 支持标记/取消收藏联系人，并进行筛选。
 **多联系方式**: 一个联系人支持添加多个电话或邮箱。
 **数据导入导出**: 支持 Excel 文件的上传导入和下载导出。
 **云端部署**: 已部署至 Render 平台，可公网访问。

## 3. 技术栈
* **后端**: Python, Flask, SQLAlchemy, Pandas
* **前端**: HTML, JavaScript, Bootstrap 5
* **数据库**: SQLite

## 4. 如何运行 (How to Run)

**本地运行:**
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

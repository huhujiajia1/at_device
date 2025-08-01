# Revit到FBX转换器

这个Python脚本可以将Revit (.rvt) 文件转换为FBX格式，使用Autodesk Platform Services (APS) API。

## 修复的问题

原始代码存在以下问题，现在已经修复：

1. **导入语句错误**：将中文的"导入"改为Python的"import"
2. **语法错误**：修复了中文标点符号和变量名
3. **缩进问题**：修正了代码缩进
4. **变量名错误**：将中文变量名改为英文
5. **作用域配置**：修正了APS API的作用域配置

## 安装依赖项

### 方法1：使用系统包管理器（推荐）
```bash
sudo apt update
sudo apt install python3-requests
```

### 方法2：使用虚拟环境
```bash
# 安装venv包
sudo apt install python3.13-venv

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖项
pip install -r requirements.txt
```

### 方法3：强制安装（不推荐）
```bash
pip3 install --break-system-packages -r requirements.txt
```

## 使用方法

1. 确保你有有效的APS凭证（CLIENT_ID和CLIENT_SECRET）
2. 运行脚本：
```bash
python3 revit_to_fbx_converter.py /path/to/your/file.rvt
```

## 功能说明

脚本会执行以下步骤：

1. **获取访问令牌**：使用APS凭证获取访问令牌
2. **创建存储桶**：在APS OSS中创建或检查存储桶
3. **上传文件**：使用Signed-S3方式上传Revit文件
4. **提交转换任务**：向Model Derivative API提交FBX转换任务
5. **轮询状态**：监控转换进度直到完成
6. **下载结果**：下载生成的FBX文件

## 注意事项

- 确保你的APS应用有足够的权限（data:read, data:write, bucket:create, bucket:read, code:all）
- 转换时间取决于文件大小和服务器负载
- 生成的FBX文件会保存在当前目录下

## 错误排查

如果遇到问题：

1. 检查APS凭证是否正确
2. 确认网络连接正常
3. 验证Revit文件格式正确
4. 查看错误信息中的详细描述
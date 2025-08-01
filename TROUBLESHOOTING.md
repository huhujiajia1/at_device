# Revit到FBX转换器故障排除指南

## 🔍 问题分析

根据你提供的错误信息，主要问题是：

```
⚠️ HTTP 400 错误 → https://developer.api.autodesk.com/modelderivative/v2/designdata/job
{'diagnostic'： 'Failed to trigger translation for this file.'}
```

这个错误通常表示APS无法处理上传的文件。

## 🛠️ 解决方案

### 1. 检查文件格式支持

APS Model Derivative API支持以下文件格式：

**Revit文件:**
- `.rvt` - Revit项目文件
- `.rfa` - Revit族文件  
- `.rte` - Revit模板文件

**其他支持格式:**
- `.dwg`, `.dxf` - AutoCAD文件
- `.ifc` - IFC文件
- `.nwd`, `.nwc` - Navisworks文件

### 2. 验证文件完整性

确保你的Revit文件：
- 没有损坏
- 是有效的Revit文件
- 文件大小合理（通常几MB到几百MB）

### 3. 检查APS权限

确保你的APS应用有以下权限：
- `data:read`
- `data:write` 
- `bucket:create`
- `bucket:read`
- `code:all`

### 4. 使用调试版本

运行调试版本来获取更详细的错误信息：

```bash
python3 debug_converter.py Room.rvt
```

### 5. 常见错误及解决方案

#### 错误1: "Failed to trigger translation"
**原因:** 文件格式不被支持或文件损坏
**解决方案:**
- 确保文件是有效的Revit文件
- 尝试使用不同版本的Revit文件
- 检查文件是否损坏

#### 错误2: HTTP 400 Bad Request
**原因:** 请求参数错误
**解决方案:**
- 检查URN格式是否正确
- 验证认证令牌是否有效
- 确认请求载荷格式正确

#### 错误3: HTTP 401 Unauthorized
**原因:** 认证失败
**解决方案:**
- 检查CLIENT_ID和CLIENT_SECRET是否正确
- 确认APS应用状态正常
- 验证作用域权限

#### 错误4: HTTP 403 Forbidden
**原因:** 权限不足
**解决方案:**
- 检查APS应用权限设置
- 确认有足够的配额
- 验证API访问权限

## 🔧 修复的代码问题

### 原始代码问题：
1. **导入语句错误**: 使用中文"导入"而不是Python的"import"
2. **语法错误**: 中文标点符号和变量名
3. **缩进问题**: 代码缩进不正确
4. **作用域配置**: 中文作用域名称

### 修复后的改进：
1. ✅ 正确的Python语法
2. ✅ 详细的错误处理
3. ✅ 调试信息输出
4. ✅ 文件格式验证
5. ✅ 更好的错误分析

## 📋 使用步骤

1. **安装依赖项:**
   ```bash
   sudo apt install python3-requests
   ```

2. **运行转换器:**
   ```bash
   python3 revit_to_fbx_converter.py Room.rvt
   ```

3. **如果遇到问题，使用调试版本:**
   ```bash
   python3 debug_converter.py Room.rvt
   ```

## 🎯 建议

1. **使用有效的Revit文件**: 确保文件是使用Revit创建的
2. **检查文件大小**: 过大的文件可能需要更长的处理时间
3. **验证网络连接**: 确保可以访问APS API
4. **查看详细日志**: 使用调试版本获取更多信息

## 📞 进一步支持

如果问题仍然存在：
1. 检查APS开发者控制台的应用状态
2. 验证API配额使用情况
3. 查看APS官方文档了解支持的文件格式
4. 联系APS技术支持
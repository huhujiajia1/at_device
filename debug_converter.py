import sys
import json
import time
import base64
import os
import requests

# APS 凭证
CLIENT_ID = "5OsaD3oEFFA5J8QoASFWVyqhVhKUDzzLiWhaLcdY4anjs1AP"
CLIENT_SECRET = "WkRxIHnMvzUow64DFvXW2DPGkAV75tsE9tehqBm4mH7Vp3AtipWNdEy1FzmSnN5m"

# 作用域
SCOPES = ["data:read", "data:write", "bucket:create", "bucket:read", "code:all"]
SCOPES_STR = " ".join(SCOPES)

# 全局常量
BUCKET_KEY = f"{CLIENT_ID.lower()}-revit-to-fbx-bucket-direct-requests"
APS_BASE_URL = "https://developer.api.autodesk.com"
AUTH_URL = f"{APS_BASE_URL}/authentication/v2/token"
OSS_URL = f"{APS_BASE_URL}/oss/v2/buckets"
MD_URL = f"{APS_BASE_URL}/modelderivative/v2"

def get_token():
    print("正在获取访问令牌...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": SCOPES_STR
    }
    r = requests.post(AUTH_URL, headers=headers, data=data, timeout=10)
    r.raise_for_status()
    print("令牌获取成功！")
    return r.json()["access_token"]

def check_file_support(file_path):
    """检查文件是否被APS支持"""
    print(f"检查文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    print(f"文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    supported_formats = ['.rvt', '.rfa', '.rte', '.dwg', '.dxf', '.ifc', '.nwd', '.nwc']
    
    if file_ext in supported_formats:
        print(f"✅ 文件格式支持: {file_ext}")
    else:
        print(f"⚠️ 文件格式可能不支持: {file_ext}")
        print(f"支持的格式: {supported_formats}")
    
    return True

def upload_and_get_urn(file_path, object_name, auth_headers):
    """上传文件并返回URN"""
    print(f"上传文件: {object_name}")
    
    # 获取预签名URL
    signed_url_ep = f"{OSS_URL}/{BUCKET_KEY}/objects/{object_name}/signeds3upload?minutes=60"
    r = requests.get(signed_url_ep, headers=auth_headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    upload_key = data["uploadKey"]
    signed_s3_url = data["urls"][0]
    
    print(f"预签名URL获取成功")
    
    # 上传到S3
    with open(file_path, "rb") as f:
        r = requests.put(
            signed_s3_url,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(os.path.getsize(file_path))
            },
            data=f,
            timeout=120
        )
        r.raise_for_status()
        print("文件上传成功")
    
    # 完成上传
    complete_ep = f"{OSS_URL}/{BUCKET_KEY}/objects/{object_name}/signeds3upload"
    complete_headers = {**auth_headers, "Content-Type": "application/json"}
    complete_body = {"uploadKey": upload_key}
    r = requests.post(complete_ep, headers=complete_headers, json=complete_body, timeout=10)
    r.raise_for_status()
    print("OSS完成回调成功")
    
    # 生成URN
    object_urn_raw = f"urn:adsk.objects:os.object:{BUCKET_KEY}/{object_name}"
    base64_urn = base64.urlsafe_b64encode(object_urn_raw.encode()).decode().rstrip("=")
    
    print(f"原始URN: {object_urn_raw}")
    print(f"Base64 URN: {base64_urn}")
    
    return base64_urn

def submit_job_with_debug(base64_urn, object_name, auth_headers):
    """提交转换任务并添加详细调试信息"""
    print("提交转换任务...")
    
    job_url = f"{MD_URL}/designdata/job"
    job_payload = {
        "input": {
            "urn": base64_urn,
        },
        "output": {
            "formats": [
                {
                    "type": "fbx",
                    "advanced": {
                        "exportFileStructure": "multiple",
                        "unit": "meter"
                    }
                }
            ]
        }
    }
    
    print(f"请求URL: {job_url}")
    print(f"请求载荷:")
    print(json.dumps(job_payload, indent=2))
    print(f"认证头: Bearer {auth_headers['Authorization'][:50]}...")
    
    try:
        r = requests.post(
            job_url, 
            headers={**auth_headers, "Content-Type": "application/json"},
            json=job_payload,
            timeout=30
        )
        
        print(f"响应状态码: {r.status_code}")
        print(f"响应头: {dict(r.headers)}")
        
        if r.status_code == 200:
            print("✅ 任务提交成功")
            return r.json()
        else:
            print(f"❌ 任务提交失败")
            print(f"响应内容: {r.text}")
            r.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e}")
        print(f"响应内容: {r.text if 'r' in locals() else 'N/A'}")
        raise
    except Exception as e:
        print(f"其他错误: {e}")
        raise

def main(file_path):
    print("=== Revit到FBX转换器调试版本 ===")
    
    # 检查文件
    if not check_file_support(file_path):
        sys.exit(1)
    
    # 获取令牌
    access_token = get_token()
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    object_name = os.path.basename(file_path)
    
    # 上传文件并获取URN
    base64_urn = upload_and_get_urn(file_path, object_name, auth_headers)
    
    # 提交转换任务
    try:
        result = submit_job_with_debug(base64_urn, object_name, auth_headers)
        print("转换任务已提交，结果:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"转换任务提交失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查文件是否为有效的Revit文件")
        print("2. 确认APS应用有足够的权限")
        print("3. 检查网络连接")
        print("4. 尝试使用不同的文件格式")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 debug_converter.py /path/to/file.rvt")
        sys.exit(1)
    main(sys.argv[1])
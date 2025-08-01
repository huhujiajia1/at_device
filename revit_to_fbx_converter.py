import sys
import json
import time
import base64
import os
import requests  # 确保已安装：pip install requests

# --- APS 凭证（建议改为读取环境变量以避免泄漏） ---
CLIENT_ID = "5OsaD3oEFFA5J8QoASFWVyqhVhKUDzzLiWhaLcdY4anjs1AP"  # 待办事项：os.getenv("APS_CLIENT_ID")
CLIENT_SECRET = "WkRxIHnMvzUow64DFvXW2DPGkAV75tsE9tehqBm4mH7Vp3AtipWNdEy1FzmSnN5m"  # 待办事项：os.getenv("APS_CLIENT_SECRET")

# --- 作用域 ---
SCOPES = ["data:read", "data:write", "bucket:create", "bucket:read", "viewables:read"]
SCOPES_STR = " ".join(SCOPES)

# --- 全局常量 ---
BUCKET_KEY = f"{CLIENT_ID.lower()}-revit-to-fbx-bucket-direct-requests"
APS_BASE_URL = "https://developer.api.autodesk.com"
AUTH_URL = f"{APS_BASE_URL}/authentication/v2/token"
OSS_URL = f"{APS_BASE_URL}/oss/v2/buckets"
MD_URL = f"{APS_BASE_URL}/modelderivative/v2"

# --------------------------------------------------------------------------- #
# 1. 获取访问令牌
# --------------------------------------------------------------------------- #
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

# --------------------------------------------------------------------------- #
# 2. 创建（或检查）存储桶
# --------------------------------------------------------------------------- #
def ensure_bucket(auth_headers):
    print(f"正在检查存储桶 '{BUCKET_KEY}'...")
    r = requests.get(f"{OSS_URL}/{BUCKET_KEY}/details", headers=auth_headers, timeout=10)
    if r.status_code == 404:
        print("存储桶不存在，正在创建...")
        payload = {"bucketKey": BUCKET_KEY, "policyKey": "temporary"}
        r = requests.post(OSS_URL, headers={**auth_headers, "Content-Type": "application/json"},
                         json=payload, timeout=10)
        r.raise_for_status()
        print("存储桶创建成功。")
    else:
        r.raise_for_status()
        print("存储桶已存在。")

# --------------------------------------------------------------------------- #
# 3. 通过 Signed-S3 上传文件并 complete
# --------------------------------------------------------------------------- #
def upload_file_via_signed_s3(file_path, object_name, auth_headers):
    print(f"正在上传文件 '{object_name}' —— 使用Signed-S3 流程")
    # 3a. 获取预签名 URL
    signed_url_ep = f"{OSS_URL}/{BUCKET_KEY}/objects/{object_name}/signeds3upload?minutesExpiration=60"
    r = requests.get(signed_url_ep, headers=auth_headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    upload_key = data["uploadKey"]  # <<< 新增：complete 步需要
    signed_s3_url = data["urls"][0]

    # 3b. 上传到 S3
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
        print("文件上传成功。")

    # 3c. **必须**调用 complete 让 OSS 可见 <<< 新增
    complete_ep = f"{OSS_URL}/{BUCKET_KEY}/objects/{object_name}/signeds3upload"  # 不带 query
    complete_headers = {**auth_headers, "Content-Type": "application/json"}  # <<< 修复
    complete_body = {"uploadKey": upload_key}  # <<< 修复
    r = requests.post(complete_ep, headers=complete_headers, json=complete_body, timeout=10)
    r.raise_for_status()
    print("OSS 完成回调成功，文件已正式可见。")
    
    # 返回符合 APS 规范的 base64-URN
    object_urn_raw = f"urn:adsk.objects:os.object:{BUCKET_KEY}/{object_name}"
    base64_urn = base64.urlsafe_b64encode(object_urn_raw.encode()).decode().rstrip("=")
    return base64_urn

# --------------------------------------------------------------------------- #
# 4. 提交转换任务
# --------------------------------------------------------------------------- #
def submit_fbx_job(base64_urn, root_filename, auth_headers):
    print("正在发起 FBX 转换任务...")
    job_url = f"{MD_URL}/designdata/job"
    job_payload = {
        "input": {
            "urn": base64_urn,
        },
        "output": {
            "formats": [
                # { # 如仅需 FBX 可删除此 SVF 块
                # "type": "svf",
                # "views": ["2d", "3d"]
                # },
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
    
    try:
        r = requests.post(job_url, headers={**auth_headers, "Content-Type": "application/json"},
                         json=job_payload)
        r.raise_for_status()
        print("转换任务已成功提交。")
    except requests.HTTPError as e:
        print("提交 Job 失败，服务端返回：")
        print(r.text)  # 让 APS 的错误码和描述都打印出来
        raise
    return

# --------------------------------------------------------------------------- #
# 5. 轮询 Manifest 直到完成
# --------------------------------------------------------------------------- #
def wait_for_job(base64_urn, auth_headers, poll_max=180, poll_interval=10):
    manifest_ep = f"{MD_URL}/designdata/{base64_urn}/manifest"
    for i in range(poll_max):
        r = requests.get(manifest_ep, headers=auth_headers, timeout=10)
        r.raise_for_status()
        manifest = r.json()
        status = manifest.get("status")
        progress = manifest.get("progress", "N/A")
        print(f" 轮询 {i+1}/{poll_max}： 状态={status}， 进度={progress}")
        if status in ("success", "failed"):
            # 保存最后的manifest到文件
            with open("last_manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            return manifest
        time.sleep(poll_interval)
    raise RuntimeError("轮询次数耗尽，任务仍未完成。")

# --------------------------------------------------------------------------- #
# 6. 下载 FBX 衍生物
# --------------------------------------------------------------------------- #
def download_fbx(manifest, base64_urn, object_name, auth_headers):
    fbx_urn = None
    for d in manifest.get("derivatives", []):
        if d.get("outputType") == "fbx":
            for ch in d.get("children", []):
                if ch.get("role") == "fbx":
                    fbx_urn = ch.get("urn")
                    break
    if not fbx_urn:
        raise RuntimeError("在 manifest 中未找到 FBX 衍生物。")

    dl_url = f"{MD_URL}/designdata/{base64_urn}/manifest/{fbx_urn}"
    r = requests.get(dl_url, headers=auth_headers, timeout=120)
    r.raise_for_status()
    local_name = f"{os.path.splitext(object_name)[0]}.fbx"
    with open(local_name, "wb") as f:
        f.write(r.content)
    print(f"已下载 FBX 文件 → {local_name}")

# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def main(rvt_path):
    if not os.path.isfile(rvt_path):
        print(f"错误：文件 '{rvt_path}' 不存在。")
        sys.exit(1)

    access_token = get_token()
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    object_name = os.path.basename(rvt_path)

    ensure_bucket(auth_headers)
    base64_urn = upload_file_via_signed_s3(rvt_path, object_name, auth_headers)  # <<< 修改：返回正确 URN
    submit_fbx_job(base64_urn, object_name, auth_headers)
    manifest = wait_for_job(base64_urn, auth_headers)
    if manifest["status"] == "success":
        download_fbx(manifest, base64_urn, object_name, auth_headers)
        print("流程完成！")
    else:
        print(json.dumps(manifest, indent=2))
        print("转换失败，请检查上方错误信息。")

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法： python revit_to_fbx_converter.py /path/to/Room.rvt")
        sys.exit(1)
    main(sys.argv[1])
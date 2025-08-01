import base64
import os

# 测试URN生成
def test_urn_generation():
    CLIENT_ID = "5OsaD3oEFFA5J8QoASFWVyqhVhKUDzzLiWhaLcdY4anjs1AP"
    BUCKET_KEY = f"{CLIENT_ID.lower()}-revit-to-fbx-bucket-direct-requests"
    object_name = "Room.rvt"
    
    # 生成URN
    object_urn_raw = f"urn:adsk.objects:os.object:{BUCKET_KEY}/{object_name}"
    base64_urn = base64.urlsafe_b64encode(object_urn_raw.encode()).decode().rstrip("=")
    
    print(f"原始URN: {object_urn_raw}")
    print(f"Base64编码: {base64_urn}")
    
    # 验证解码
    decoded = base64.urlsafe_b64decode(base64_urn + "=" * (4 - len(base64_urn) % 4)).decode()
    print(f"解码验证: {decoded}")
    print(f"编码正确: {decoded == object_urn_raw}")
    
    return base64_urn

if __name__ == "__main__":
    test_urn_generation()
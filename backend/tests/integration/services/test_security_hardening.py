import pytest
import os
import zipfile
import io
from pathlib import Path
from fastapi import UploadFile
from app.services.ontology_service import OntologyService
from app.repositories.ontology_repo import OntologyRepository
from app.repositories.webhook_repo import WebhookRepository

@pytest.mark.integration
class TestSecurityHardening:
    """
    针对安全加固功能的集成测试：
    1. 验证恶意路径 (Zip Slip) 被拦截
    2. 验证文件数量超限被拦截
    3. 验证解压总大小超限被拦截
    """

    @pytest.fixture
    def ontology_service(self, test_db_session):
        onto_repo = OntologyRepository(test_db_session)
        webhook_repo = WebhookRepository(test_db_session)
        return OntologyService(onto_repo, webhook_repo)

    def test_zip_slip_prevention(self, ontology_service, temp_storage_dir):
        """测试路径遍历攻击防御"""
        # 构造一个包含恶意路径的 ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('../../evil.txt', 'danger')
        buf.seek(0)
        
        extract_path = temp_storage_dir / "test_slip"
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(buf, 'r') as zf:
            # 应该记录报警日志，但不会解压到 extract_path 之外
            ontology_service._safe_extract(zf, str(extract_path))
            
        evil_file = temp_storage_dir.parent / "evil.txt"
        assert not evil_file.exists(), "恶意文件不应存在于目标目录之外"

    def test_too_many_files_prevention(self, ontology_service, temp_storage_dir):
        """测试文件数量超限限制"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            # 超过 MAX_FILE_COUNT (1000)
            for i in range(1005):
                zf.writestr(f'file_{i}.txt', 'content')
        buf.seek(0)
        
        extract_path = temp_storage_dir / "test_count"
        os.makedirs(extract_path, exist_ok=True)
        
        with pytest.raises(ValueError) as exc:
            with zipfile.ZipFile(buf, 'r') as zf:
                ontology_service._safe_extract(zf, str(extract_path))
        
        assert "文件数量过多" in str(exc.value)

    def test_zip_bomb_size_prevention(self, ontology_service, temp_storage_dir):
        """测试解压总大小超限限制"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            # 写入一个解压后超过 500MB 的文件
            # 制造 501MB 的垃圾数据
            # 为节省测试运行时的内存，我们可以分块写入
            # 但 zipfile.writestr 会一次性接收数据，所以这里我们用两个较大的文件组合
            # 每个文件 260MB，总计 520MB
            data_chunk = b'0' * (260 * 1024 * 1024)
            zf.writestr('large_1.txt', data_chunk)
            zf.writestr('large_2.txt', data_chunk)
            
        buf.seek(0)
        extract_path = temp_storage_dir / "test_bomb"
        os.makedirs(extract_path, exist_ok=True)
        
        with pytest.raises(ValueError) as exc:
            with zipfile.ZipFile(buf, 'r') as zf:
                ontology_service._safe_extract(zf, str(extract_path))
                
        assert "总大小超过限制" in str(exc.value)

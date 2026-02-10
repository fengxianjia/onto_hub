from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from ...models import OntologyFile, OntologyEntity

class BaseParser(ABC):
    """
    本体文件解析器基类
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """该解析器支持的文件扩展名列表 (例如: ['.md', '.markdown'])"""
        pass

    @abstractmethod
    def parse(self, file_record: OntologyFile, content: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析文件内容并返回实体记录列表
        
        Args:
            file_record: 数据库中的文件记录对象
            content: 文件原文内容
            rules: 解析模板规则字典
            
        Returns:
            List[Dict]: 实体记录列表。每个字典应包含:
                - metadata (Dict): 提取出的属性字典
                - links (List[str]): 提取出的关系目标名称或 URI 列表
                - body (str): 提取出的主体内容 (可选)
                - name (str): 显式指定的实体名称 (可选, 插件可覆盖核心命名逻辑)
                - category (str): 显式指定的实体类别 (可选)
        """
        pass

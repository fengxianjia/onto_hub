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
    def parse(self, file_record: OntologyFile, content: str, rules: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        解析文件内容
        
        Args:
            file_record: 数据库中的文件记录对象
            content: 文件原文内容
            rules: 解析模板规则字典
            
        Returns:
            Tuple[metadata, wikilinks]: 
                - metadata: 提取出的属性字典 (将存入 metadata_json)
                - wikilinks: 提取出的 Wiki 链接列表 (用于构建关系)
        """
        pass

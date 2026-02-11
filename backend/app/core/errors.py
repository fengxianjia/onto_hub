from fastapi import HTTPException, status
from .results import ServiceResult, ServiceStatus

class BusinessCode:
    # 本体相关
    ONTOLOGY_ALREADY_EXISTS = "ONTOLOGY_ALREADY_EXISTS"
    ONTOLOGY_NAME_ALREADY_EXISTS = "ONTOLOGY_NAME_ALREADY_EXISTS"
    ONTOLOGY_NOT_FOUND = "ONTOLOGY_NOT_FOUND"
    
    # 模板相关
    TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
    TEMPLATE_DUPLICATE = "TEMPLATE_DUPLICATE"
    TEMPLATE_NAME_DUPLICATE = "TEMPLATE_NAME_DUPLICATE"
    
    # Webhook 相关
    WEBHOOK_NOT_FOUND = "WEBHOOK_NOT_FOUND"
    WEBHOOK_DUPLICATE = "WEBHOOK_DUPLICATE"
    WEBHOOK_NAME_DUPLICATE = "WEBHOOK_NAME_DUPLICATE"
    
    # 通用
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    ACTION_FORBIDDEN = "ACTION_FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND" 
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_IN_USE = "RESOURCE_IN_USE"
    VERSION_ACTIVE = "VERSION_ACTIVE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class BusinessException(HTTPException):
    def __init__(self, business_code: str, detail: str = None, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)
        self.business_code = business_code

def handle_result(result: ServiceResult):
    """
    统一处理 ServiceResult 并转换为 BusinessException。
    如果结果成功，则返回数据；否则抛出对应的业务异常。
    """
    if result.success:
        return result.data
        
    status_map = {
        ServiceStatus.NOT_FOUND: (BusinessCode.RESOURCE_NOT_FOUND, 404),
        ServiceStatus.ALREADY_EXISTS: (BusinessCode.VALIDATION_ERROR, 400),
        ServiceStatus.DUPLICATE_NAME: (BusinessCode.VALIDATION_ERROR, 400),
        ServiceStatus.RESOURCE_IN_USE: (BusinessCode.RESOURCE_IN_USE, 400),
        ServiceStatus.VERSION_ACTIVE: (BusinessCode.VERSION_ACTIVE, 400),
        ServiceStatus.BAD_REQUEST: (BusinessCode.VALIDATION_ERROR, 400),
        ServiceStatus.FAILURE: (BusinessCode.INTERNAL_ERROR, 500),
    }
    
    # 默认映射
    b_code, s_code = status_map.get(result.status, (BusinessCode.INTERNAL_ERROR, 500))
    
    # 如果 ServiceResult 自带了更精细的 business_code，则覆盖默认值
    if result.business_code:
        b_code = result.business_code
    
    raise BusinessException(
        business_code=b_code,
        detail=result.message or "操作失败",
        status_code=s_code
    )

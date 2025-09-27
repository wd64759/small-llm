import sys
import project_root_finder
from pydantic import BaseModel, Field
from typing import Optional, Type

PROJECT_ROOT = project_root_finder.root.as_posix()
sys.path.append(PROJECT_ROOT)

from utils.dbhelper import DBHelper

class FundSelectionSchema(BaseModel):
    """基金选择工具输入参数模型"""
    risk_level: Optional[str] = Field(None, description="风险等级：支持'R1-R5'、'1-5'、'保守型'、'稳健型'、'中性型'、'积极型'、'激进型'。查询时会返回指定风险等级以内的所有基金产品")
    fund_type: Optional[str] = Field(None, description="基金类型：支持'商品基金'、'债券型'、'混合型'、'股票型'、'QDII'、'基金中基金（FOF）'")
    fund_manager: Optional[str] = Field(None, description="基金经理姓名")
    fund_company: Optional[str] = Field(None, description="基金公司名称")
    fund_name: Optional[str] = Field(None, description="基金名称（支持模糊查询）")
    fund_code: Optional[str] = Field(None, description="基金代码")
    
    # 收益率筛选条件
    yearly_return_min: Optional[float] = Field(None, description="最近1年收益率最小值")
    total_return_min: Optional[float] = Field(None, description="成立以来收益率最小值")
    
    # 风险指标筛选条件
    sharpe_ratio_max: Optional[float] = Field(None, description="夏普比率最大值(百分位)")

from langchain_core.tools import StructuredTool

class FundSelectionTool(StructuredTool):
    name: str = "fund_selection"
    description: str = "基金选择工具"
    args_schema: Type[BaseModel] = FundSelectionSchema

    def _run(self, risk_level: Optional[str] = None, fund_type: Optional[str] = None, fund_manager: Optional[str] = None, fund_company: Optional[str] = None, fund_name: Optional[str] = None, fund_code: Optional[str] = None, yearly_return_min: Optional[float] = None, total_return_min: Optional[float] = None, sharpe_ratio_max: Optional[float] = None)->dict:
        dbhelper = DBHelper()
        
        # 基础查询
        query = "SELECT * FROM cityark.fund_info WHERE 1=1"
        params = []
        
        # 使用字典映射定义条件和参数
        conditions = {
            'risk_level': ('risk_level = %s', risk_level),
            'fund_type': ('fund_type = %s', fund_type),
            'fund_manager': ('fund_manager = %s', fund_manager),
            'fund_company': ('fund_company = %s', fund_company),
            'fund_name': ('fund_name LIKE %s', f"%{fund_name}%" if fund_name else None),
            'fund_code': ('fund_code = %s', fund_code),
            'yearly_return_min': ('yearly_return >= %s', yearly_return_min),
            'total_return_min': ('total_return >= %s', total_return_min),
            'sharpe_ratio_max': ('sharpe_ratio <= %s', sharpe_ratio_max)
        }
        
        # 动态添加条件
        for field, (condition, value) in conditions.items():
            if value is not None:
                query += f" AND {condition}"
                params.append(value)
        
        rs = dbhelper.execute_query(query, params)
        return rs

if __name__ == "__main__":
    dbhelper = DBHelper()
    rs = dbhelper.execute_query("SELECT * FROM cityark.fund_info limit 10") 
    print(rs)
    dbhelper.close_connection(rs)

"""Excel数据读取工具"""

import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger


class ExcelReader:
    """Excel文件读取器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data: Optional[pd.DataFrame] = None
        self._validate_file()
    
    def _validate_file(self):
        """验证文件是否存在且为Excel格式"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel文件不存在: {self.file_path}")
        
        if self.file_path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"不支持的文件格式: {self.file_path.suffix}")
    
    def load_data(self, sheet_name: str = 0, **kwargs) -> pd.DataFrame:
        """加载Excel数据
        
        Args:
            sheet_name: 工作表名称或索引
            **kwargs: pandas.read_excel的其他参数
        
        Returns:
            DataFrame: 加载的数据
        """
        try:
            self.data = pd.read_excel(
                self.file_path, 
                sheet_name=sheet_name,
                **kwargs
            )
            logger.info(f"成功加载Excel文件: {self.file_path}, 数据行数: {len(self.data)}")
            return self.data
        except Exception as e:
            logger.error(f"加载Excel文件失败: {e}")
            raise
    
    def get_test_cases(self, 
                      id_column: str = "ID",
                      input_column: str = "输入", 
                      expected_column: str = "期望输出",
                      expected_extract_path_column: str = "期望提取路径",
                      actual_extract_path_column: str = "实际提取路径") -> List['TestCase']:
        """获取LLM测试用例列表
        
        Args:
            id_column: ID列名
            input_column: 输入列名
            expected_column: 期望输出列名
            expected_extract_path_column: 期望结果JSON提取路径列名
            actual_extract_path_column: 实际结果JSON提取路径列名
        
        Returns:
            List[TestCase]: 测试用例列表
        """
        if self.data is None:
            raise ValueError("请先加载Excel文件")
        
        test_cases = []
        
        for index, row in self.data.iterrows():
            # 获取测试用例ID，如果没有则使用行号
            test_id = row.get(id_column, f"test_{index + 1}")
            
            # 获取输入和期望输出
            input_text = str(row.get(input_column, "")).strip()
            expected_text = str(row.get(expected_column, "")).strip()
            
            # 获取提取路径参数
            expected_extract_path = str(row.get(expected_extract_path_column, "$")).strip()
            actual_extract_path = str(row.get(actual_extract_path_column, "$")).strip()
            
            # 处理空值或nan值
            if expected_extract_path in ["", "nan", "None"]:
                expected_extract_path = "$"
            if actual_extract_path in ["", "nan", "None"]:
                actual_extract_path = "$"
            
            # 跳过空行
            if not input_text and not expected_text:
                continue
            
            # 导入TestCase
            from ..llm_test import TestCase
            
            test_case = TestCase(
                id=str(test_id),
                input=input_text,
                expected=expected_text,
                metadata={
                    'expected_extract_path': expected_extract_path,
                    'actual_extract_path': actual_extract_path
                }
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def get_http_test_cases(self,
                           id_column: str = "ID",
                           method_column: str = "方法",
                           endpoint_column: str = "端点",
                           expected_column: str = "期望响应",
                           headers_column: str = "请求头",
                           body_column: str = "请求体",
                           expected_status_column: str = "期望状态码",
                           expected_extract_path_column: str = "期望提取路径",
                           actual_extract_path_column: str = "实际提取路径") -> List['HTTPTestCase']:
        """获取HTTP测试用例列表
        
        Args:
            id_column: ID列名
            method_column: HTTP方法列名
            endpoint_column: 端点URL列名
            expected_column: 期望响应列名
            headers_column: 请求头列名
            body_column: 请求体列名
            expected_status_column: 期望状态码列名
            expected_extract_path_column: 期望结果JSON提取路径列名
            actual_extract_path_column: 实际结果JSON提取路径列名
        
        Returns:
            List[HTTPTestCase]: HTTP测试用例列表
        """
        if self.data is None:
            raise ValueError("请先加载Excel文件")
        
        # 导入HTTPTestCase
        from ..http_test import HTTPTestCase
        import json
        
        test_cases = []
        
        for index, row in self.data.iterrows():
            # 获取测试用例ID
            test_id = row.get(id_column, f"http_test_{index + 1}")
            
            # 获取基本信息
            method = str(row.get(method_column, "GET")).strip().upper()
            endpoint = str(row.get(endpoint_column, "")).strip()
            expected = str(row.get(expected_column, "")).strip()
            
            # 跳过空行
            if not endpoint:
                continue
            
            # 处理请求头
            headers = None
            headers_str = str(row.get(headers_column, "")).strip()
            if headers_str and headers_str != "nan":
                try:
                    headers = json.loads(headers_str)
                except json.JSONDecodeError:
                    logger.warning(f"测试用例 {test_id}: 请求头格式错误，将忽略")
            
            # 处理请求体
            body = None
            body_str = str(row.get(body_column, "")).strip()
            if body_str and body_str != "nan":
                if method in ['POST', 'PUT', 'PATCH']:
                    try:
                        # 尝试解析为JSON
                        body = json.loads(body_str)
                    except json.JSONDecodeError:
                        # 如果不是JSON，作为字符串处理
                        body = body_str
            
            # 处理期望状态码
            expected_status_code = None
            status_str = str(row.get(expected_status_column, "")).strip()
            if status_str and status_str != "nan":
                try:
                    expected_status_code = int(float(status_str))
                except (ValueError, TypeError):
                    logger.warning(f"测试用例 {test_id}: 期望状态码格式错误，将使用默认值200")
            
            # 处理JSON提取路径
            expected_extract_path = "$"  # 默认值
            actual_extract_path = "$"    # 默认值
            
            expected_path_str = str(row.get(expected_extract_path_column, "")).strip()
            if expected_path_str and expected_path_str != "nan":
                expected_extract_path = expected_path_str
            
            actual_path_str = str(row.get(actual_extract_path_column, "")).strip()
            if actual_path_str and actual_path_str != "nan":
                actual_extract_path = actual_path_str
            
            test_case = HTTPTestCase(
                id=str(test_id),
                method=method,
                endpoint=endpoint,
                headers=headers,
                data=body,
                expected=expected,
                expected_status_code=expected_status_code,
                metadata={
                    "expected_extract_path": expected_extract_path,
                    "actual_extract_path": actual_extract_path
                }
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def get_column_names(self) -> List[str]:
        """获取所有列名"""
        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        return list(self.data.columns)
    
    def get_data_info(self) -> Dict[str, Any]:
        """获取数据基本信息"""
        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        
        return {
            'file_path': str(self.file_path),
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': self.data.dtypes.to_dict(),
            'null_counts': self.data.isnull().sum().to_dict()
        }
    
    def validate_test_data(self, 
                          input_column: str = '输入', 
                          expected_column: str = '期望输出') -> Dict[str, Any]:
        """验证测试数据的完整性
        
        Args:
            input_column: 输入列名
            expected_column: 期望输出列名
        
        Returns:
            Dict: 验证结果
        """
        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 检查必需列是否存在
        required_columns = [input_column, expected_column]
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"缺少必需的列: {missing_columns}")
        
        # 检查空值
        for col in required_columns:
            if col in self.data.columns:
                null_count = self.data[col].isnull().sum()
                if null_count > 0:
                    validation_result['warnings'].append(f"列 '{col}' 有 {null_count} 个空值")
        
        # 统计信息
        validation_result['statistics'] = {
            'total_rows': len(self.data),
            'valid_rows': len(self.data.dropna(subset=required_columns)),
            'duplicate_rows': self.data.duplicated().sum()
        }
        
        return validation_result


class BatchExcelReader:
    """批量Excel文件读取器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")
    
    def find_excel_files(self) -> List[Path]:
        """查找目录下的所有Excel文件"""
        excel_files = []
        for pattern in ['*.xlsx', '*.xls']:
            excel_files.extend(self.data_dir.glob(pattern))
        return sorted(excel_files)
    
    def load_all_files(self, **kwargs) -> Dict[str, pd.DataFrame]:
        """加载所有Excel文件
        
        Returns:
            Dict: 文件名到DataFrame的映射
        """
        excel_files = self.find_excel_files()
        if not excel_files:
            logger.warning(f"在目录 {self.data_dir} 中未找到Excel文件")
            return {}
        
        data_dict = {}
        for file_path in excel_files:
            try:
                reader = ExcelReader(file_path)
                data = reader.load_data(**kwargs)
                data_dict[file_path.stem] = data
                logger.info(f"成功加载文件: {file_path.name}")
            except Exception as e:
                logger.error(f"加载文件 {file_path.name} 失败: {e}")
        
        return data_dict
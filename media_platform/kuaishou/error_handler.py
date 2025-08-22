# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

import sys
from datetime import datetime
from typing import Optional
from playwright.async_api import Page

from tools import utils


class ErrorHandler:
    """错误处理工具类"""
    
    def __init__(self, page: Page, enable_screenshots: bool = True):
        self.page = page
        self.enable_screenshots = enable_screenshots
        
    def _generate_screenshot_path(self, action: str) -> str:
        """生成截图路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"/tmp/kuaishou_{action}_{timestamp}.png"
    
    async def handle_login_button_failure(self):
        """处理登录按钮点击失败的错误"""
        utils.logger.error("[ErrorHandler] 所有点击方法都失败了")
        
        if self.enable_screenshots:
            await self._take_screenshot("login_failed")
    
    async def handle_qrcode_not_found(self):
        """处理二维码未找到的错误"""
        utils.logger.error("[ErrorHandler] 未找到二维码，登录失败")
        
        if self.enable_screenshots:
            await self._take_screenshot("no_qrcode")
            
        # 打印页面内容用于调试
        await self._log_page_debug_info()
        
        # 退出程序
        sys.exit()
    
    async def _take_screenshot(self, action: str) -> Optional[str]:
        """截取页面截图"""
        try:
            screenshot_path = self._generate_screenshot_path(action)
            await self.page.screenshot(path=screenshot_path)
            utils.logger.info(f"[ErrorHandler] 已保存截图到: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            utils.logger.warning(f"[ErrorHandler] 截图失败: {e}")
            return None
    
    async def _log_page_debug_info(self):
        """记录页面调试信息"""
        try:
            # 打印页面内容长度
            page_content = await self.page.content()
            utils.logger.debug(f"[ErrorHandler] 页面内容长度: {len(page_content)}")
            
            # 查找可能的二维码相关元素
            qr_elements = await self.page.query_selector_all(
                "*[class*='qr'], *[class*='code'], img"
            )
            utils.logger.info(f"[ErrorHandler] 找到可能相关的元素数量: {len(qr_elements)}")
            
            # 记录页面标题和URL
            title = await self.page.title()
            url = self.page.url
            utils.logger.debug(f"[ErrorHandler] 页面标题: {title}")
            utils.logger.debug(f"[ErrorHandler] 页面URL: {url}")
            
        except Exception as e:
            utils.logger.warning(f"[ErrorHandler] 获取页面调试信息失败: {e}")
    
    async def handle_general_error(self, error_msg: str, action: str = "error"):
        """处理一般性错误"""
        utils.logger.error(f"[ErrorHandler] {error_msg}")
        
        if self.enable_screenshots:
            await self._take_screenshot(action)
    
    def log_success(self, message: str):
        """记录成功信息"""
        utils.logger.info(f"[ErrorHandler] ✓ {message}")
    
    def log_warning(self, message: str):
        """记录警告信息"""
        utils.logger.warning(f"[ErrorHandler] ⚠ {message}")
    
    def log_error(self, message: str):
        """记录错误信息"""
        utils.logger.error(f"[ErrorHandler] ✗ {message}") 
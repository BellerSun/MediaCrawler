# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

import asyncio
from typing import Optional, List, Any
from playwright.async_api import Page

from tools import utils


class ClickHandler:
    """点击处理工具类"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def click_with_multiple_methods(
        self, 
        element: Any, 
        methods: List[dict],
        retry_interval: int = 1
    ) -> bool:
        """
        使用多种方法尝试点击元素
        
        Args:
            element: 要点击的元素
            methods: 点击方法配置列表
            retry_interval: 重试间隔(秒)
            
        Returns:
            是否点击成功
        """
        for method_config in methods:
            try:
                method_name = method_config["name"]
                utils.logger.info(f"[ClickHandler] 尝试{method_name}...")
                
                success = await self._execute_click_method(element, method_config)
                
                if success:
                    utils.logger.info(f"[ClickHandler] {method_name}成功")
                    return True
                    
            except Exception as e:
                utils.logger.warning(f"[ClickHandler] {method_config['name']}失败: {e}")
                await asyncio.sleep(retry_interval)
        
        return False
    
    async def _execute_click_method(self, element: Any, method_config: dict) -> bool:
        """执行具体的点击方法"""
        method_type = method_config["method"]
        force = method_config.get("force", False)
        
        try:
            if method_type == "standard":
                if force:
                    await element.click(force=True)
                else:
                    await element.click()
                    
            elif method_type == "javascript":
                await element.evaluate("element => element.click()")
                
            elif method_type == "mouse":
                await element.click(button="left", click_count=1)
                
            elif method_type == "delayed":
                await asyncio.sleep(2)
                await element.click(force=True)
                
            else:
                utils.logger.warning(f"[ClickHandler] 未知的点击方法: {method_type}")
                return False
                
            return True
            
        except Exception as e:
            utils.logger.debug(f"[ClickHandler] 点击方法 {method_type} 执行失败: {e}")
            return False
    
    async def try_javascript_fallback(self) -> bool:
        """尝试JavaScript回退方案"""
        try:
            utils.logger.info("[ClickHandler] 最后尝试：直接JavaScript点击...")
            await self.page.evaluate("""
                const buttons = Array.from(document.querySelectorAll('p, span, div, button'));
                const loginBtn = buttons.find(btn => btn.textContent && btn.textContent.includes('登录'));
                if (loginBtn) {
                    loginBtn.click();
                    console.log('JavaScript点击成功');
                    return true;
                } else {
                    console.log('未找到登录按钮');
                    return false;
                }
            """)
            utils.logger.info("[ClickHandler] JavaScript点击执行完成")
            return True
            
        except Exception as e:
            utils.logger.error(f"[ClickHandler] JavaScript点击也失败了: {e}")
            return False
    
    async def check_for_overlay_and_click_force(self, element: Any) -> bool:
        """
        检查是否有遮罩层，如果有则直接使用强制点击
        
        Args:
            element: 要点击的元素
            
        Returns:
            是否成功处理遮罩层问题
        """
        try:
            # 检查是否有遮罩层
            overlays = await self.page.query_selector_all(
                "div[style*='z-index'], div[class*='mask'], div[class*='overlay']"
            )
            
            if len(overlays) > 0:
                utils.logger.info(f"[ClickHandler] 检测到 {len(overlays)} 个可能的遮罩层，使用强制点击")
                await element.click(force=True)
                return True
            else:
                utils.logger.info("[ClickHandler] 未检测到遮罩层")
                return False
                
        except Exception as e:
            utils.logger.warning(f"[ClickHandler] 遮罩层检测失败: {e}")
            return False


class PageStateChecker:
    """页面状态检查工具类"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def check_page_state(self) -> bool:
        """检查页面状态"""
        try:
            # 检查页面标题
            title = await self.page.title()
            utils.logger.info(f"[PageStateChecker] 页面标题: {title}")
            
            # 检查页面URL
            url = self.page.url
            utils.logger.info(f"[PageStateChecker] 当前URL: {url}")
            
            # 检查页面是否加载完成
            ready_state = await self.page.evaluate("document.readyState")
            utils.logger.info(f"[PageStateChecker] 页面加载状态: {ready_state}")
            
            # 检查是否有遮罩层
            overlays = await self.page.query_selector_all(
                "div[style*='z-index'], div[class*='mask'], div[class*='overlay']"
            )
            utils.logger.info(f"[PageStateChecker] 发现可能的遮罩层数量: {len(overlays)}")
            
            return True
            
        except Exception as e:
            utils.logger.error(f"[PageStateChecker] 检查页面状态失败: {e}")
            return False
    
    async def wait_for_page_load(self, wait_seconds: int = 3):
        """等待页面加载完成"""
        utils.logger.info(f"[PageStateChecker] 等待页面加载完成...({wait_seconds}秒)")
        await asyncio.sleep(wait_seconds)
        
    async def wait_for_dialog(self, wait_seconds: int = 2):
        """等待对话框出现"""
        utils.logger.info(f"[PageStateChecker] 等待登录对话框出现...({wait_seconds}秒)")
        await asyncio.sleep(wait_seconds) 
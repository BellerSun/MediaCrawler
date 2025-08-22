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
from typing import Optional, List, Tuple, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from tools import utils
from tools.crawler_util import find_login_qrcode


class ElementFinder:
    """元素查找工具类"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def find_element_with_selectors(
        self, 
        selectors: List[str], 
        timeout_ms: int = 5000,
        concurrent: bool = False
    ) -> Optional[Any]:
        """
        使用多个选择器查找元素
        
        Args:
            selectors: 选择器列表
            timeout_ms: 超时时间(毫秒)
            concurrent: 是否并发查找
            
        Returns:
            找到的第一个元素，如果都没找到返回None
        """
        if concurrent:
            return await self._find_element_concurrent(selectors, timeout_ms)
        else:
            return await self._find_element_sequential(selectors, timeout_ms)
    
    async def _find_element_sequential(
        self, 
        selectors: List[str], 
        timeout_ms: int
    ) -> Optional[Any]:
        """顺序查找元素"""
        for i, selector in enumerate(selectors):
            try:
                utils.logger.info(f"[ElementFinder] 尝试选择器 {i+1}/{len(selectors)}: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=timeout_ms)
                if element:
                    # 检查元素状态
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    utils.logger.info(f"[ElementFinder] 元素状态 - 可见: {is_visible}, 可用: {is_enabled}")
                    
                    if is_visible and is_enabled:
                        utils.logger.info(f"[ElementFinder] 成功找到元素，使用选择器: {selector}")
                        return element
                        
            except PlaywrightTimeoutError:
                utils.logger.warning(f"[ElementFinder] 选择器 {selector} 超时")
            except Exception as e:
                utils.logger.warning(f"[ElementFinder] 选择器 {selector} 出错: {e}")
        
        return None
    
    async def _find_element_concurrent(
        self, 
        selectors: List[str], 
        timeout_ms: int
    ) -> Optional[Any]:
        """并发查找元素"""
        utils.logger.info(f"[ElementFinder] 并发查找元素，使用 {len(selectors)} 个选择器")
        
        # 创建并发任务
        tasks = []
        for i, selector in enumerate(selectors):
            task = asyncio.create_task(
                self._try_find_single_element(selector, timeout_ms, i+1, len(selectors)),
                name=f"selector_{i}_{selector}"
            )
            tasks.append(task)
        
        try:
            # 等待第一个成功的结果
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout_ms / 1000.0
            )
            
            # 取消剩余的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 检查完成的任务结果
            for task in done:
                try:
                    result = await task
                    if result is not None:
                        utils.logger.info(f"[ElementFinder] 并发查找成功，使用任务: {task.get_name()}")
                        return result
                except Exception as e:
                    utils.logger.warning(f"[ElementFinder] 任务 {task.get_name()} 失败: {e}")
                    
        except asyncio.TimeoutError:
            utils.logger.warning(f"[ElementFinder] 并发查找超时 {timeout_ms}ms")
            # 取消所有任务
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        return None
    
    async def _try_find_single_element(
        self, 
        selector: str, 
        timeout_ms: int, 
        index: int, 
        total: int
    ) -> Optional[Any]:
        """尝试查找单个元素"""
        try:
            utils.logger.info(f"[ElementFinder] 并发尝试选择器 {index}/{total}: {selector}")
            element = await self.page.wait_for_selector(selector, timeout=timeout_ms)
            if element:
                # 检查元素状态
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                if is_visible and is_enabled:
                    utils.logger.info(f"[ElementFinder] 选择器 {selector} 找到可用元素")
                    return element
                else:
                    utils.logger.info(f"[ElementFinder] 选择器 {selector} 元素不可用 - 可见: {is_visible}, 可用: {is_enabled}")
                        
        except PlaywrightTimeoutError:
            utils.logger.debug(f"[ElementFinder] 选择器 {selector} 超时")
        except asyncio.CancelledError:
            utils.logger.debug(f"[ElementFinder] 选择器 {selector} 被取消")
        except Exception as e:
            utils.logger.warning(f"[ElementFinder] 选择器 {selector} 出错: {e}")
        
        return None


class QRCodeFinder:
    """二维码查找工具类"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def find_qrcode_with_selectors(
        self, 
        selectors: List[str], 
        timeout_ms: int = 30000,
        concurrent: bool = False
    ) -> Optional[str]:
        """
        使用多个选择器查找二维码
        
        Args:
            selectors: 选择器列表
            timeout_ms: 超时时间(毫秒)
            concurrent: 是否并发查找
            
        Returns:
            二维码的base64数据，如果都没找到返回None
        """
        if concurrent:
            return await self._find_qrcode_concurrent(selectors, timeout_ms)
        else:
            return await self._find_qrcode_sequential(selectors, timeout_ms)
    
    async def _find_qrcode_sequential(
        self, 
        selectors: List[str], 
        timeout_ms: int
    ) -> Optional[str]:
        """顺序查找二维码"""
        for i, selector in enumerate(selectors):
            try:
                utils.logger.info(f"[QRCodeFinder] 尝试二维码选择器 {i+1}/{len(selectors)}: {selector}")
                base64_qrcode_img = await find_login_qrcode(self.page, selector=selector, timeout=timeout_ms)
                if base64_qrcode_img:
                    utils.logger.info(f"[QRCodeFinder] 成功找到二维码，使用选择器: {selector}")
                    return base64_qrcode_img
            except Exception as e:
                utils.logger.warning(f"[QRCodeFinder] 二维码选择器 {selector} 失败: {e}")
        
        return None
    
    async def _find_qrcode_concurrent(
        self, 
        selectors: List[str], 
        timeout_ms: int
    ) -> Optional[str]:
        """并发查找二维码"""
        utils.logger.info(f"[QRCodeFinder] 并发查找二维码，使用 {len(selectors)} 个选择器")
        
        # 创建并发任务
        tasks = []
        for i, selector in enumerate(selectors):
            task = asyncio.create_task(
                self._try_find_single_qrcode(selector, i+1, len(selectors), timeout_ms),
                name=f"qrcode_{i}_{selector}"
            )
            tasks.append(task)
        
        try:
            # 等待第一个成功的结果
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout_ms / 1000.0
            )
            
            # 取消剩余的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 检查完成的任务结果
            for task in done:
                try:
                    result = await task
                    if result is not None:
                        utils.logger.info(f"[QRCodeFinder] 并发查找成功，使用任务: {task.get_name()}")
                        return result
                except Exception as e:
                    utils.logger.warning(f"[QRCodeFinder] 任务 {task.get_name()} 失败: {e}")
                    
        except asyncio.TimeoutError:
            utils.logger.warning(f"[QRCodeFinder] 并发查找超时 {timeout_ms}ms")
            # 取消所有任务
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        return None
    
    async def _try_find_single_qrcode(
        self, 
        selector: str, 
        index: int, 
        total: int,
        timeout_ms: int = 30000
    ) -> Optional[str]:
        """尝试查找单个二维码"""
        try:
            utils.logger.info(f"[QRCodeFinder] 并发尝试二维码选择器 {index}/{total}: {selector}")
            base64_qrcode_img = await find_login_qrcode(self.page, selector=selector, timeout=timeout_ms)
            if base64_qrcode_img:
                utils.logger.info(f"[QRCodeFinder] 选择器 {selector} 找到二维码")
                return base64_qrcode_img
                        
        except asyncio.CancelledError:
            utils.logger.debug(f"[QRCodeFinder] 选择器 {selector} 被取消")
        except Exception as e:
            utils.logger.warning(f"[QRCodeFinder] 选择器 {selector} 出错: {e}")
        
        return None 
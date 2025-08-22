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
import functools
import sys
from typing import Optional

from playwright.async_api import BrowserContext, Page
from tenacity import (RetryError, retry, retry_if_result, stop_after_attempt,
                      wait_fixed)

import config
from base.base_crawler import AbstractLogin
from tools import utils

# 导入新的工具类
from .login_config import KuaishouLoginConfig
from .element_finder import ElementFinder, QRCodeFinder
from .click_handler import ClickHandler, PageStateChecker
from .error_handler import ErrorHandler
from .optimized_config import get_config_by_environment


class KuaishouLogin(AbstractLogin):
    def __init__(self,
                 login_type: str,
                 browser_context: BrowserContext,
                 context_page: Page,
                 login_phone: Optional[str] = "",
                 cookie_str: str = "",
                 enable_concurrent: bool = True,  # 是否启用并发优化
                 optimization_level: str = "balanced"  # 新增：优化级别
                 ):
        config.LOGIN_TYPE = login_type
        self.browser_context = browser_context
        self.context_page = context_page
        self.login_phone = login_phone
        self.cookie_str = cookie_str
        self.enable_concurrent = enable_concurrent
        
        # 根据优化级别选择配置
        if enable_concurrent and optimization_level != "concurrent":
            utils.logger.info(f"[KuaishouLogin] 启用并发模式，自动使用并发优化配置")
            optimization_level = "concurrent"
        
        # 初始化优化配置
        self.config = get_config_by_environment(optimization_level)
        utils.logger.info(f"[KuaishouLogin] 使用 '{optimization_level}' 优化配置")
        
        # 初始化工具类
        self.element_finder = ElementFinder(context_page)
        self.qrcode_finder = QRCodeFinder(context_page)
        self.click_handler = ClickHandler(context_page)
        self.page_checker = PageStateChecker(context_page)
        self.error_handler = ErrorHandler(context_page)
        
        # 打印配置信息
        self._log_config_info()

    def _log_config_info(self):
        """打印当前使用的配置信息"""
        utils.logger.info(f"[KuaishouLogin] 配置信息:")
        utils.logger.info(f"[KuaishouLogin] - 登录按钮超时: {self.config.timeouts.login_button_selector}ms")
        utils.logger.info(f"[KuaishouLogin] - 二维码超时: {self.config.timeouts.qrcode_selector}ms") 
        utils.logger.info(f"[KuaishouLogin] - 点击超时: {self.config.timeouts.click_element}ms")
        utils.logger.info(f"[KuaishouLogin] - 重试间隔: {self.config.timeouts.click_retry_interval}s")
        utils.logger.info(f"[KuaishouLogin] - 并发模式: {'启用' if self.enable_concurrent else '禁用'}")

    async def begin(self):
        """Start login xiaohongshu"""
        utils.logger.info("[KuaishouLogin.begin] Begin login kuaishou ...")
        if config.LOGIN_TYPE == "qrcode":
            await self.login_by_qrcode()
        elif config.LOGIN_TYPE == "phone":
            await self.login_by_mobile()
        elif config.LOGIN_TYPE == "cookie":
            await self.login_by_cookies()
        else:
            raise ValueError("[KuaishouLogin.begin] Invalid Login Type Currently only supported qrcode or phone or cookie ...")

    @retry(stop=stop_after_attempt(600), wait=wait_fixed(1), retry=retry_if_result(lambda value: value is False))
    async def check_login_state(self) -> bool:
        """
            Check if the current login status is successful and return True otherwise return False
            retry decorator will retry 20 times if the return value is False, and the retry interval is 1 second
            if max retry times reached, raise RetryError
        """
        current_cookie = await self.browser_context.cookies()
        _, cookie_dict = utils.convert_cookies(current_cookie)
        kuaishou_pass_token = cookie_dict.get("passToken")
        if kuaishou_pass_token:
            return True
        return False

    async def login_by_qrcode(self):
        """登录快手网站并保持登录状态 - 重构版本"""
        utils.logger.info("[KuaishouLogin.login_by_qrcode] Begin login kuaishou by qrcode ...")
        
        # 1. 检查页面状态
        await self.page_checker.check_page_state()
        
        # 2. 等待页面完全加载
        await self.page_checker.wait_for_page_load(self.config.timeouts.page_load_wait)
        
        # 3. 查找登录按钮
        login_button_ele = await self._find_login_button()
        
        # 4. 点击登录按钮
        click_success = await self._click_login_button(login_button_ele)
        
        if not click_success:
            await self.error_handler.handle_login_button_failure()
            # 尝试JavaScript回退方案
            await self.click_handler.try_javascript_fallback()
                
        # 5. 等待登录弹窗出现
        await self.page_checker.wait_for_dialog(self.config.timeouts.login_dialog_wait)
        
        # 6. 再次检查页面状态
        await self.page_checker.check_page_state()

        # 7. 查找二维码
        base64_qrcode_img = await self._find_qrcode()
        
        if not base64_qrcode_img:
            await self.error_handler.handle_qrcode_not_found()

        # 8. 显示二维码
        await self._show_qrcode(base64_qrcode_img)

        # 9. 等待扫码登录
        await self._wait_for_login_completion()

        # 10. 等待重定向
        await self._wait_for_redirect()

    async def _find_login_button(self):
        """查找登录按钮"""
        utils.logger.info("[KuaishouLogin] 开始查找登录按钮...")
        
        login_button_ele = await self.element_finder.find_element_with_selectors(
            selectors=self.config.selectors.login_buttons,
            timeout_ms=self.config.timeouts.login_button_selector,
            concurrent=self.enable_concurrent
        )
        
        if not login_button_ele:
            # 尝试原始选择器作为最后的备选
            utils.logger.warning("[KuaishouLogin] 使用原始选择器作为备选...")
            login_button_ele = self.context_page.locator("xpath=//p[text()='登录']")
            
        return login_button_ele

    async def _click_login_button(self, login_button_ele) -> bool:
        """点击登录按钮"""
        utils.logger.info("[KuaishouLogin] 开始尝试点击登录按钮...")
        
        # 首先尝试检查遮罩层并强制点击
        if await self.click_handler.check_for_overlay_and_click_force(login_button_ele):
            return True
        
        # 如果没有遮罩层或强制点击失败，使用多种方法尝试
        return await self.click_handler.click_with_multiple_methods(
            element=login_button_ele,
            methods=self.config.strategies.click_methods,
            retry_interval=self.config.timeouts.click_retry_interval
        )

    async def _find_qrcode(self) -> Optional[str]:
        """查找二维码"""
        utils.logger.info("[KuaishouLogin] 开始查找二维码...")
        
        return await self.qrcode_finder.find_qrcode_with_selectors(
            selectors=self.config.selectors.qrcode_images,
            timeout_ms=self.config.timeouts.qrcode_selector,
            concurrent=self.enable_concurrent
        )

    async def _show_qrcode(self, base64_qrcode_img: str):
        """显示二维码"""
        utils.logger.info("[KuaishouLogin] 显示二维码...")
        partial_show_qrcode = functools.partial(utils.show_qrcode, base64_qrcode_img)
        asyncio.get_running_loop().run_in_executor(executor=None, func=partial_show_qrcode)

    async def _wait_for_login_completion(self):
        """等待扫码登录完成"""
        utils.logger.info(f"[KuaishouLogin.login_by_qrcode] waiting for scan code login, remaining time is 20s")
        try:
            await self.check_login_state()
            self.error_handler.log_success("扫码登录成功")
        except RetryError:
            utils.logger.info("[KuaishouLogin.login_by_qrcode] Login kuaishou failed by qrcode login method ...")
            sys.exit()

    async def _wait_for_redirect(self):
        """等待页面重定向"""
        wait_redirect_seconds = self.config.timeouts.redirect_wait
        utils.logger.info(f"[KuaishouLogin.login_by_qrcode] Login successful then wait for {wait_redirect_seconds} seconds redirect ...")
        await asyncio.sleep(wait_redirect_seconds)

    async def login_by_mobile(self):
        pass

    async def login_by_cookies(self):
        utils.logger.info("[KuaishouLogin.login_by_cookies] Begin login kuaishou by cookie ...")
        for key, value in utils.convert_str_cookie_to_dict(self.cookie_str).items():
            await self.browser_context.add_cookies([{
                'name': key,
                'value': value,
                'domain': ".kuaishou.com",
                'path': "/"
            }])

    # ===== 为了兼容性保留的旧方法 =====
    # 这些方法现在被新的工具类替代，但为了不破坏现有代码保留

    async def _try_click_with_multiple_methods(self, login_button_ele):
        """兼容性方法：使用新的点击处理器"""
        return await self.click_handler.click_with_multiple_methods(
            element=login_button_ele,
            methods=self.config.strategies.click_methods,
            retry_interval=self.config.timeouts.click_retry_interval
        )

    async def _delayed_click(self, element):
        """兼容性方法：延迟点击方法"""
        await asyncio.sleep(2)
        await element.click(force=True)

    async def _check_page_state(self):
        """兼容性方法：使用新的页面状态检查器"""
        return await self.page_checker.check_page_state()

    async def _wait_for_login_button(self):
        """兼容性方法：使用新的元素查找器"""
        return await self.element_finder.find_element_with_selectors(
            selectors=self.config.selectors.login_buttons,
            timeout_ms=self.config.timeouts.login_button_selector,
            concurrent=False  # 兼容性模式下不使用并发
        )
